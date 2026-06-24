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
import log as L
import queue as Q

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
                "ledger_row_num": row_num,
                "extraction_snapshot": {
                    "gates": role["extraction"].get("gates", {}),
                    "variables": role["extraction"].get("variables", {}),
                },
            })
            _VERDICT_INDEX.setdefault(key, set()).add(verdict_id)
        return self._send_json(200, {"verdict_id": verdict_id, "ledger_row_num": row_num})


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
