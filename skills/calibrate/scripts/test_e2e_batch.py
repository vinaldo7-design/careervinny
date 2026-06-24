#!/usr/bin/env python3
"""End-to-end: propose -> apply (accept + defer + reject) -> assert audit + state."""
import http.client, json, os, shutil, socket, tempfile, threading, time
import server as S
import batch_state as B
import defer_queue as DQ

fails = []
def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        fails.append(name)


def _free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]; s.close(); return p


def _seed_repo(root, key="alpha-strategy-manager"):
    d = os.path.join(root, "state", "roles", key); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "jd.md"), "w").write(
        "---\ncompany: Alpha\ntitle: Strategy Manager\nlocation: London\nposting-age: 2 days\n"
        "source-url: https://example.com/a\ndomain: consulting:ai-strategy\n---\nbody\n")
    open(os.path.join(d, "extraction.json"), "w").write(json.dumps({
        "gates": {"visa-sponsorship": "pass"},
        "variables": {"client-facing": {"verdict": "UNMET", "quote": ""},
                      "frontier-strategy": {"verdict": "MET", "quote": "x"}}}))
    open(os.path.join(d, "score.md"), "w").write(
        "---\nrubric-version: 3\nfit: 80\nband: safety\nscreen: pass\nodds: 0.6\n---\nbody")
    os.makedirs(os.path.join(root, "reference"), exist_ok=True)
    open(os.path.join(root, "reference", "fit-rubric.md"), "w").write(
        "---\nrubric-version: 3\n---\n\n"
        "| id | variable | kind | weight | floor | how-to-read |\n"
        "|----|----------|------|--------|-------|-------------|\n"
        "| frontier-strategy | Frontier | spine | 30 | 0.4 | ... |\n"
        "| mgmt-ladder | Mgmt ladder | spine | 20 | 0.4 | ... |\n"
        "| client-facing | Client facing | heavy | 10 | — | ... |\n")
    check_dir = os.path.join(root, "skills", "score-fit", "scripts"); os.makedirs(check_dir, exist_ok=True)
    open(os.path.join(check_dir, "check.sh"), "w").write("#!/bin/sh\nexit 0\n"); os.chmod(os.path.join(check_dir, "check.sh"), 0o755)
    open(os.path.join(root, "calibration-ledger.md"), "w").write(
        "# Ledger\n\n| # | role | verdict | why | rubric band | GAP |\n"
        "|---|------|---------|-----|-------------|-----|\n")
    open(os.path.join(root, "calibration-log.jsonl"), "w").close()
    return key


def _start(root, port):
    t = threading.Thread(target=S.run, args=(root, port, False), daemon=True); t.start()
    for _ in range(40):
        try:
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=0.5)
            c.request("GET", "/health"); c.getresponse().read(); c.close(); return
        except Exception:
            time.sleep(0.05)
    raise RuntimeError("server did not start")


def post(port, path, payload):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    c.request("POST", path, body=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    r = c.getresponse(); b = r.read().decode(); c.close()
    return r.status, b


# GREEN propose -> apply flow with mixed accept/defer/reject
root = tempfile.mkdtemp(prefix="e2e-"); key = _seed_repo(root)
try:
    port = _free_port(); _start(root, port)
    bid_before = B.current_batch_id(root)
    # 3 pursue verdicts that should produce client-facing weight-up
    for _ in range(3):
        post(port, "/verdict", {"role_key": key, "verdict": "pursue", "reason": "x"})
    s, body = post(port, "/batch/propose", {"force": True, "force_reason": "e2e"})
    check("/batch/propose 200", s == 200)
    prop = json.loads(body)
    check("at least one card", len(prop["cards"]) >= 1)
    card = prop["cards"][0]
    s, body = post(port, "/batch/apply", {"accept_ids": [card["proposal_id"]], "reject_ids": [], "defer_ids": []})
    d = json.loads(body)
    check("apply: status=applied", d["status"] == "applied")
    check("apply: one weight applied", len(d["applied"]) == 1)
    check("counter advanced", B.current_batch_id(root) == bid_before + 1)
    audit = os.path.join(root, d["audit_path"])
    check("audit file written", os.path.exists(audit))
finally:
    shutil.rmtree(root)


# DEFER carry-through: defer a card in batch 1, see it re-surface in batch 2
root = tempfile.mkdtemp(prefix="e2e-d-"); key = _seed_repo(root)
try:
    port = _free_port(); _start(root, port)
    for _ in range(3):
        post(port, "/verdict", {"role_key": key, "verdict": "pursue", "reason": "x"})
    s, body = post(port, "/batch/propose", {"force": True, "force_reason": "defer-test"})
    prop = json.loads(body)
    pid = prop["cards"][0]["proposal_id"]
    post(port, "/batch/apply", {"accept_ids": [], "reject_ids": [], "defer_ids": [pid]})
    deferred = DQ.currently_deferred(root)
    check("after defer: one deferred", len(deferred) == 1)
    # Open new batch, post a verdict, propose -> deferred shows up
    post(port, "/verdict", {"role_key": key, "verdict": "no", "reason": "y"})
    s2, body2 = post(port, "/batch/propose", {"force": True, "force_reason": "round-2"})
    prop2 = json.loads(body2)
    check("deferred card re-surfaces", any(c["proposal_id"] == pid for c in prop2["deferred"]))
finally:
    shutil.rmtree(root)


# RED apply -> revert + counter unchanged
root = tempfile.mkdtemp(prefix="e2e-r-"); key = _seed_repo(root)
try:
    cs = os.path.join(root, "skills", "score-fit", "scripts", "check.sh")
    open(cs, "w").write("#!/bin/sh\necho FAIL alpha-strategy-manager\nexit 1\n"); os.chmod(cs, 0o755)
    port = _free_port(); _start(root, port)
    bid_before = B.current_batch_id(root)
    rubric_before = open(os.path.join(root, "reference", "fit-rubric.md")).read()
    for _ in range(3):
        post(port, "/verdict", {"role_key": key, "verdict": "pursue", "reason": "x"})
    s, body = post(port, "/batch/propose", {"force": True, "force_reason": "red"})
    prop = json.loads(body)
    pid = prop["cards"][0]["proposal_id"]
    s, body = post(port, "/batch/apply", {"accept_ids": [pid], "reject_ids": [], "defer_ids": []})
    d = json.loads(body)
    check("red: status=reverted", d["status"] == "reverted")
    check("red: rubric reverted byte-for-byte", open(os.path.join(root, "reference", "fit-rubric.md")).read() == rubric_before)
    check("red: counter NOT advanced", B.current_batch_id(root) == bid_before)
    check("red: contradicting roles surfaced", len(d["contradicting_roles"]) >= 1)
finally:
    shutil.rmtree(root)


print()
print("FAILED:", fails if fails else "none")
raise SystemExit(1 if fails else 0)
