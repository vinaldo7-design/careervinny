#!/usr/bin/env python3
"""Calibration dashboard HTTP server. Stdlib only.

Anti-anchoring is the ONLY non-trivial business rule: GET /score/<key> returns 423 unless
the request carries a verdict_id that the log can prove was already written for that role.
"""
import datetime
import http.server
import json
import os
import re
import secrets
import sys
import threading
import urllib.parse
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "score-fit", "scripts"))
import batch_state as B
import log as L
import queue as Q
import review as REV
import proposals as PR
import apply_proposals as AP
import defer_queue as DQ
import scorer as SCORER

REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
TEMPLATE_PATH = os.path.join(HERE, "templates", "index.html")
STATIC_DIR = os.path.join(HERE, "static")

_LOCK = threading.Lock()
_VERDICT_INDEX = {}  # role_key -> set of issued verdict_ids; rebuilt at startup


def _current_rubric_version(repo_root):
    p = os.path.join(repo_root, "reference", "fit-rubric.md")
    if not os.path.exists(p):
        return "unknown"
    text = open(p, encoding="utf-8").read()
    m = re.search(r"(?m)^rubric-version:\s*(\S+)", text)
    return m.group(1) if m else "unknown"


def _last_log_rubric(repo_root):
    p = os.path.join(repo_root, "calibration-log.jsonl")
    if not os.path.exists(p):
        return None
    last = None
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            last = json.loads(line)
        except json.JSONDecodeError:
            print(f'WARN: skipped malformed line in {p}', flush=True)
            continue
    return (last or {}).get("rubric_version")


def _rebuild_index(repo_root):
    p = os.path.join(repo_root, "calibration-log.jsonl")
    _VERDICT_INDEX.clear()
    if not os.path.exists(p):
        return
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            print(f'WARN: skipped malformed line in {p}', flush=True)
            continue
        _VERDICT_INDEX.setdefault(row.get("role_key", ""), set()).add(row.get("verdict_id", ""))


def _pre_verdict_payload(repo_root, key):
    """JSON for the role page WITHOUT any score fields (anti-anchoring)."""
    full = Q.load_role(repo_root, key)
    jd_fm = {}
    text = full["jd_md"]
    m = re.search(r"^---\n(.*?)\n---", text, re.S)
    if m:
        for ln in m.group(1).splitlines():
            mm = re.match(r"^([a-zA-Z_-]+):\s*(.*)$", ln)
            if mm:
                jd_fm[mm.group(1)] = mm.group(2).strip()
    extraction = full["extraction"]
    # Build fit_rows from extraction variables (each variable is a row without score magnitude)
    fit_rows = [
        {"variable": var, "verdict": info.get("verdict", ""), "quote": info.get("quote", "")}
        for var, info in extraction.get("variables", {}).items()
    ]
    # prestige from extraction or JD frontmatter
    prestige = extraction.get("prestige") or jd_fm.get("prestige") or ""
    # ALREADY_LABELLED: check if this role_key has been verdicted before
    already_labelled = key in Q._already_labelled(repo_root)
    return {
        "key": key,
        "company": jd_fm.get("company", ""),
        "title": jd_fm.get("title", ""),
        "location": jd_fm.get("location", ""),
        "posting_age": jd_fm.get("posting-age", ""),
        "jd_link": jd_fm.get("source-url") or ("/jd/" + key),
        "jd_md": full["jd_md"],
        "extraction": extraction,
        "screen_gates": extraction.get("gates", {}),
        "fit_rows": fit_rows,
        "prestige": prestige,
        "ALREADY_LABELLED": already_labelled,
    }


def _score_payload(repo_root, key):
    full = Q.load_role(repo_root, key)
    fm = full["score_frontmatter"]
    return {"key": key, "fit": fm.get("fit"), "odds": fm.get("odds"),
            "band": fm.get("band"), "screen": fm.get("screen"),
            "rubric_version": fm.get("rubric-version"),
            "score_md": full["score_md"]}


class Handler(http.server.BaseHTTPRequestHandler):
    repo_root = REPO_ROOT

    def log_message(self, fmt, *a):
        return  # quiet

    def _send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, status, body, ctype="text/html; charset=utf-8"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        p, qs = u.path, urllib.parse.parse_qs(u.query)
        if p == "/health":
            return self._send_json(200, {"ok": True})
        if p == "/count":
            n = 0
            lp = os.path.join(self.repo_root, "calibration-log.jsonl")
            if os.path.exists(lp):
                n = sum(1 for ln in open(lp, encoding="utf-8") if ln.strip())
            return self._send_json(200, {"count": n})
        if p == "/batch-summary":
            lp = os.path.join(self.repo_root, "calibration-log.jsonl")
            rows = []
            if os.path.exists(lp):
                for line in open(lp, encoding="utf-8"):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            window_param = (qs.get("window") or [None])[0]
            if window_param is None or window_param == "":
                selected = rows[-Q.BATCH_SIZE:]
            elif window_param == "all":
                selected = rows
            else:
                try:
                    n = int(window_param)
                    selected = rows[-n:]
                except ValueError:
                    return self._send_json(400, {"error": "invalid window: must be a positive integer or 'all'"})
            return self._send_json(200, REV.batch_summary(selected, repo_root=self.repo_root))
        if p == "/":
            return self._serve_index()
        if p.startswith("/role/"):
            key = p[len("/role/"):]
            try:
                return self._send_json(200, _pre_verdict_payload(self.repo_root, key))
            except FileNotFoundError:
                return self._send_json(404, {"error": "role not found"})
        if p.startswith("/score/"):
            key = p[len("/score/"):]
            vid = (qs.get("after") or [""])[0]
            with _LOCK:
                unlocked = bool(vid and vid in _VERDICT_INDEX.get(key, set()))
            if unlocked:
                return self._send_json(200, _score_payload(self.repo_root, key))
            return self._send_json(423, {"error": "locked until verdict logged"})
        if p.startswith("/jd/"):
            key = p[len("/jd/"):]
            # Path traversal containment: reject keys that escape roles/ directory
            if '..' in key or key.startswith('/') or os.sep in key:
                return self._send_json(400, {"error": "invalid role key"})
            roles_base = os.path.normpath(os.path.join(self.repo_root, "state", "roles"))
            jd = os.path.normpath(os.path.join(roles_base, key, "jd.md"))
            if not jd.startswith(roles_base + os.sep):
                return self._send_json(400, {"error": "invalid role key"})
            if os.path.exists(jd):
                return self._send_text(200, open(jd, encoding="utf-8").read(),
                                       "text/plain; charset=utf-8")
            return self._send_text(404, "not found", "text/plain")
        if p.startswith("/static/"):
            name = os.path.basename(p)
            fp = os.path.join(STATIC_DIR, name)
            if os.path.exists(fp):
                ctype = "text/css" if name.endswith(".css") else "application/javascript"
                return self._send_text(200, open(fp, "rb").read(), ctype + "; charset=utf-8")
            return self._send_text(404, "not found", "text/plain")
        if p == "/batch/current":
            bid = B.current_batch_id(self.repo_root)
            n = 0
            lp = os.path.join(self.repo_root, "calibration-log.jsonl")
            if os.path.exists(lp):
                with open(lp, encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            if json.loads(line).get("batch_id") == bid:
                                n += 1
                        except json.JSONDecodeError:
                            continue
            return self._send_json(200, {"batch_id": bid, "verdicts_in_batch": n})
        if p == "/queue/preview":
            q = Q.build_queue(self.repo_root)
            STRIP = {"fit", "band", "screen", "odds", "jd_path"}
            clean_roles = [{k: v for k, v in r.items() if k not in STRIP} for r in q]
            industries = {}
            for r in q:
                ind = r.get("industry", "unknown")
                industries[ind] = industries.get(ind, 0) + 1
            n = len(q) or 1
            industry_list = [{"industry": k, "count": v, "pct": round(100.0 * v / n, 1)}
                             for k, v in sorted(industries.items(), key=lambda kv: (-kv[1], kv[0]))]
            return self._send_json(200, {
                "batch_id": B.current_batch_id(self.repo_root),
                "n_roles": len(q),
                "industries": industry_list,
                "roles": clean_roles,
            })
        if p.startswith("/batch/audit/"):
            try:
                n = int(p[len("/batch/audit/"):])
            except ValueError:
                return self._send_json(400, {"error": "batch id must be int"})
            fp = os.path.join(self.repo_root, "state", "batches", str(n), "calibration.md")
            if not os.path.exists(fp):
                return self._send_text(404, "audit not found", "text/plain")
            with open(fp, encoding="utf-8") as fh:
                return self._send_text(200, fh.read(), "text/markdown; charset=utf-8")
        return self._send_text(404, "not found", "text/plain")

    def _serve_index(self):
        q = Q.build_queue(self.repo_root)
        first = q[0]["key"] if q else ""
        rubric_version = _current_rubric_version(self.repo_root)
        last_rubric = _last_log_rubric(self.repo_root)
        rubric_changed = bool(last_rubric and last_rubric != rubric_version)
        # Anti-anchoring: strip score fields before injecting into page
        q_clean = [{k: v for k, v in row.items() if k not in ('fit', 'band', 'screen', 'odds')} for row in q]
        try:
            tpl = open(TEMPLATE_PATH, encoding="utf-8").read()
        except FileNotFoundError:
            return self._send_json(503, {"error": "UI not yet built"})
        # Use JSON encoding for XSS-safe inline JS substitutions
        tpl = tpl.replace("__QUEUE_JSON__", json.dumps(q_clean, ensure_ascii=True))
        tpl = tpl.replace("__FIRST_KEY__", json.dumps(first, ensure_ascii=True))
        tpl = tpl.replace("__RUBRIC_VERSION__", json.dumps(rubric_version, ensure_ascii=True))
        tpl = tpl.replace("__RUBRIC_CHANGED__", "true" if rubric_changed else "false")
        self._send_text(200, tpl)

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/batch/propose":
            payload = self._read_json_body()
            if payload is None:
                return  # _read_json_body already sent the error response
            return self._handle_batch_propose(bool(payload.get("force")), (payload.get("force_reason") or "").strip())
        if u.path == "/batch/apply":
            payload = self._read_json_body()
            if payload is None:
                return
            return self._handle_batch_apply(payload)
        if u.path != "/verdict":
            return self._send_json(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", "0") or "0")
        MAX_BODY = 1 * 1024 * 1024  # 1 MB
        if length > MAX_BODY:
            return self._send_json(413, {"error": "payload too large"})
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except Exception:
            return self._send_json(400, {"error": "bad json"})
        key = payload.get("role_key") or ""
        verdict = payload.get("verdict") or ""
        reason = payload.get("reason") or ""
        ack = bool(payload.get("ack_rubric_changed"))
        if verdict not in ("pursue", "on-ramp", "no"):
            return self._send_json(400, {"error": "verdict must be pursue|on-ramp|no"})
        if not key or not reason.strip():
            return self._send_json(400, {"error": "role_key and reason are required"})
        with _LOCK:
            current = _current_rubric_version(self.repo_root)
            last = _last_log_rubric(self.repo_root)
            if last and last != current and not ack:
                return self._send_json(409, {
                    "error": "rubric-version changed since last log row (%s -> %s); "
                             "ack_rubric_changed=true to override" % (last, current)})
            try:
                role = Q.load_role(self.repo_root, key)
            except FileNotFoundError:
                return self._send_json(404, {"error": "role not found"})
            jd_fm = {}
            m = re.search(r"^---\n(.*?)\n---", role["jd_md"], re.S)
            if m:
                for ln in m.group(1).splitlines():
                    mm = re.match(r"^([a-zA-Z_-]+):\s*(.*)$", ln)
                    if mm:
                        jd_fm[mm.group(1)] = mm.group(2).strip()
            verdict_id = secrets.token_hex(8)
            row_num = L.count_ledger_rows(self.repo_root) + 1
            ledger_line = L.format_ledger_row(row_num, {
                "key": key, "company": jd_fm.get("company", ""),
                "title": jd_fm.get("title", "")},
                verdict, reason, current)
            L.append_ledger(self.repo_root, ledger_line)
            sc = role["score_frontmatter"]
            L.append_log(self.repo_root, {
                "ts": datetime.datetime.utcnow().isoformat() + "Z",
                "role_key": key,
                "company": jd_fm.get("company", ""),
                "title": jd_fm.get("title", ""),
                "verdict": verdict,
                "reason": reason.strip(),
                "rubric_version": current,
                "machine_screen": sc.get("screen"),
                "machine_fit": sc.get("fit"),
                "machine_odds": sc.get("odds"),
                "machine_band": sc.get("band"),
                "verdict_id": verdict_id,
                "batch_id": B.current_batch_id(self.repo_root),
                "ledger_row_num": row_num,
                "extraction_snapshot": {
                    "gates": role["extraction"].get("gates", {}),
                    "variables": role["extraction"].get("variables", {}),
                },
            })
            _VERDICT_INDEX.setdefault(key, set()).add(verdict_id)
        return self._send_json(200, {"verdict_id": verdict_id, "ledger_row_num": row_num})


    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length > 1024 * 1024:
            self._send_json(413, {"error": "payload too large"})
            return None
        try:
            return json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except Exception:
            self._send_json(400, {"error": "bad json"})
            return None

    def _load_batch_rows(self):
        bid = B.current_batch_id(self.repo_root)
        rows = []
        lp = os.path.join(self.repo_root, "calibration-log.jsonl")
        if os.path.exists(lp):
            with open(lp, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if r.get("batch_id") == bid:
                        rows.append(r)
        return bid, rows

    def _load_decided_roles(self):
        """For downstream re-band: load all roles that have a score.md AND have been verdicted."""
        roles_dir = os.path.join(self.repo_root, "state", "roles")
        if not os.path.isdir(roles_dir):
            return []
        # Set of verdicted role keys
        verdicted = set()
        lp = os.path.join(self.repo_root, "calibration-log.jsonl")
        if os.path.exists(lp):
            with open(lp, encoding="utf-8") as fh:
                for line in fh:
                    try:
                        r = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if r.get("role_key"):
                        verdicted.add(r["role_key"])
        out = []
        for key in sorted(os.listdir(roles_dir)):
            if key not in verdicted:
                continue
            try:
                full = Q.load_role(self.repo_root, key)
            except FileNotFoundError:
                continue
            out.append({
                "role_key": key,
                "extraction": full.get("extraction") or {},
                "jd_body": full.get("jd_md", ""),
                "score_md_band": (full.get("score_frontmatter") or {}).get("band"),
            })
        return out

    def _past_gate_fires(self):
        # MVP: empty (review.py doesn't track per-batch gate fires yet).
        return {"_consecutive_zero_batches": {}}

    def _handle_batch_propose(self, force, force_reason):
        with _LOCK:
            bid, rows = self._load_batch_rows()
            if len(rows) == 0:
                return self._send_json(409, {"error": "batch is empty"})
            if not force and len(rows) < 20:
                return self._send_json(409, {"error": "batch has %d verdicts; need 20 or force=true with reason" % len(rows)})
            rubric = SCORER.load_rubric(os.path.join(self.repo_root, "reference", "fit-rubric.md"))
            decided = self._load_decided_roles()
            new_cards = PR.compute_proposals(rows, rubric, decided_roles=decided,
                                              past_gate_fires=self._past_gate_fires(),
                                              repo_root=self.repo_root)
            deferred_carry = DQ.currently_deferred(self.repo_root)
            deferred_cards = []
            for d in deferred_carry:
                card = dict(d["payload"] or {})
                card["proposal_id"] = d["proposal_id"]
                card["deferred_from_batch"] = d["batch_id"]
                deferred_cards.append(card)
            mix = {"pursue": 0, "on-ramp": 0, "no": 0}
            for r in rows:
                v = r.get("verdict")
                if v in mix:
                    mix[v] += 1
            return self._send_json(200, {
                "batch_id": bid,
                "n_verdicts": len(rows),
                "force": force,
                "force_reason": force_reason,
                "verdict_mix": mix,
                "cards": new_cards,
                "deferred": deferred_cards,
            })

    def _handle_batch_apply(self, payload):
        accept_ids = list(payload.get("accept_ids") or [])
        reject_ids = list(payload.get("reject_ids") or [])
        defer_ids = list(payload.get("defer_ids") or [])
        with _LOCK:
            bid, rows = self._load_batch_rows()
            # Recompute the same proposal set (deterministic). We need the full proposal dict for each
            # accept_id to know kind/var_id/magnitude.
            rubric = SCORER.load_rubric(os.path.join(self.repo_root, "reference", "fit-rubric.md"))
            decided = self._load_decided_roles()
            new_cards = PR.compute_proposals(rows, rubric, decided_roles=decided,
                                              past_gate_fires=self._past_gate_fires(),
                                              repo_root=self.repo_root)
            deferred_carry = DQ.currently_deferred(self.repo_root)
            id_to_card = {c["proposal_id"]: c for c in new_cards}
            for d in deferred_carry:
                id_to_card[d["proposal_id"]] = dict(d["payload"] or {}, proposal_id=d["proposal_id"])

            # Record events first (defer + reject) so we don't lose decisions if apply fails.
            for pid in defer_ids:
                DQ.record_event(self.repo_root, pid, "deferred", batch_id=bid, payload=id_to_card.get(pid))
            for pid in reject_ids:
                DQ.record_event(self.repo_root, pid, "rejected", batch_id=bid)

            unknown_ids = [pid for pid in accept_ids if pid not in id_to_card]
            if unknown_ids:
                return self._send_json(400, {"error": "unknown accept_ids", "unresolved_accept_ids": unknown_ids})
            accepted = [id_to_card[pid] for pid in accept_ids]
            rubric_path = os.path.join(self.repo_root, "reference", "fit-rubric.md")
            check_cmd = os.path.join(self.repo_root, "skills", "score-fit", "scripts", "check.sh")
            result = AP.apply(accepted, rubric_path, check_cmd)

            # Audit
            audit_dir = os.path.join(self.repo_root, "state", "batches", str(bid))
            os.makedirs(audit_dir, exist_ok=True)
            audit_path_rel = os.path.join("state", "batches", str(bid), "calibration.md")
            audit_full = os.path.join(audit_dir, "calibration.md")
            mix = {"pursue": 0, "on-ramp": 0, "no": 0}
            for r in rows:
                v = r.get("verdict")
                if v in mix:
                    mix[v] += 1
            with open(audit_full, "w", encoding="utf-8") as fh:
                fh.write("# Batch %d calibration audit\n\n" % bid)
                fh.write("- Verdicts: %d\n" % len(rows))
                fh.write("- Verdict mix: pursue=%d on-ramp=%d no=%d\n" % (mix["pursue"], mix["on-ramp"], mix["no"]))
                fh.write("- Guard status: %s\n\n" % result["status"])
                fh.write("## Accepted (weight)\n\n")
                if result.get("applied"):
                    for a in result["applied"]:
                        fh.write("- `%s` %s by %d (%s -> %s)\n" % (a["var_id"], a["kind"], a.get("magnitude"),
                                                                    a.get("old_weight"), a.get("new_weight")))
                else:
                    fh.write("(none)\n")
                fh.write("\n## Accepted (gate — manual)\n\n")
                if result.get("gate_decisions"):
                    for g in result["gate_decisions"]:
                        fh.write("- `%s` %s\n" % (g.get("var_id"), g.get("kind")))
                    fh.write("\nUser accepted these gate proposals; the rubric was NOT auto-edited. Make the structural edit by hand.\n")
                else:
                    fh.write("(none)\n")
                fh.write("\n## Rejected\n\n")
                for pid in reject_ids:
                    card = id_to_card.get(pid, {})
                    fh.write("- `%s` (kind=%s var=%s)\n" % (pid, card.get("kind"), card.get("var_id")))
                if not reject_ids:
                    fh.write("(none)\n")
                fh.write("\n## Deferred (will resurface next batch)\n\n")
                for pid in defer_ids:
                    card = id_to_card.get(pid, {})
                    fh.write("- `%s` (kind=%s var=%s)\n" % (pid, card.get("kind"), card.get("var_id")))
                if not defer_ids:
                    fh.write("(none)\n")
                if result.get("contradicting_roles"):
                    fh.write("\n## Contradicting roles (guard went red — rubric reverted)\n\n")
                    for k in result["contradicting_roles"]:
                        fh.write("- `%s`\n" % k)

            # Record accepted events AFTER apply (so we know guard outcome)
            for pid in accept_ids:
                status = "accepted" if result["status"] != "reverted" else "deferred"
                DQ.record_event(self.repo_root, pid, status, batch_id=bid,
                                payload=id_to_card.get(pid) if status == "deferred" else None)

            next_id = bid
            if result["status"] != "reverted":
                next_id = B.advance_batch_id(self.repo_root)
                B.snapshot_rubric(self.repo_root, next_id)

            return self._send_json(200, {
                "status": result["status"],
                "applied": result.get("applied", []),
                "skipped": result.get("skipped", []),
                "gate_decisions": result.get("gate_decisions", []),
                "contradicting_roles": result.get("contradicting_roles", []),
                "audit_path": audit_path_rel,
                "batch_id_closed": bid,
                "batch_id_next": next_id,
            })


def run(repo_root, port=8765, open_browser=True):
    Handler.repo_root = repo_root
    _rebuild_index(repo_root)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    if open_browser:
        try:
            webbrowser.open_new_tab("http://127.0.0.1:%d/" % port)
        except Exception:
            pass
    srv.serve_forever()


if __name__ == "__main__":
    run(REPO_ROOT)
