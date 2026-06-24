#!/usr/bin/env python3
"""End-to-end server tests using http.client against the real ThreadingHTTPServer.
Validates anti-anchoring: /score/<key> is 423 BEFORE /verdict and 200 AFTER."""
import http.client
import json
import os
import shutil
import socket
import tempfile
import threading
import time

import server as S

fails = []
def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        fails.append(name)


def _free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]; s.close(); return port


def _seed(root, key="alpha-strategy-manager"):
    d = os.path.join(root, "state", "roles", key)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "jd.md"), "w", encoding="utf-8").write(
        "---\ncompany: Alpha\ntitle: Strategy Manager\nlocation: London\n"
        "posting-age: 2 days\nsource-url: https://example.com/role\n---\n\nJD body here.\n")
    open(os.path.join(d, "extraction.json"), "w").write(json.dumps({
        "gates": {"visa-sponsorship": "pass", "location-uk": "pass"},
        "variables": {"frontier-strategy": {"verdict": "MET", "quote": "AI strategy"}}}))
    open(os.path.join(d, "score.md"), "w", encoding="utf-8").write(
        "---\nrubric-version: 3\nfit: 88\nband: safety\nscreen: pass\n---\nBODY\n")
    os.makedirs(os.path.join(root, "reference"), exist_ok=True)
    if not os.path.exists(os.path.join(root, "reference", "fit-rubric.md")):
        open(os.path.join(root, "reference", "fit-rubric.md"), "w", encoding="utf-8").write(
            "---\nrubric-version: 3\n---\n# rubric\n")
    if not os.path.exists(os.path.join(root, "calibration-ledger.md")):
        open(os.path.join(root, "calibration-ledger.md"), "w", encoding="utf-8").write(
            "# Ledger\n\n| # | role | verdict | why | rubric band | GAP |\n"
            "|---|------|---------|-----|-------------|-----|\n")
    if not os.path.exists(os.path.join(root, "calibration-log.jsonl")):
        open(os.path.join(root, "calibration-log.jsonl"), "w").close()
    return key


def _start_server(root, port):
    t = threading.Thread(target=S.run, args=(root, port, False), daemon=True)
    t.start()
    for _ in range(40):
        try:
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=0.5)
            c.request("GET", "/health"); c.getresponse().read(); c.close(); return
        except Exception:
            time.sleep(0.05)
    raise RuntimeError("server did not start")


root = tempfile.mkdtemp(prefix="cal-srv-")
key = _seed(root)
port = _free_port()
_start_server(root, port)


def get(path):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    c.request("GET", path)
    r = c.getresponse(); body = r.read().decode("utf-8"); c.close()
    return r.status, body


def post(path, payload):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    body = json.dumps(payload).encode("utf-8")
    c.request("POST", path, body=body, headers={"Content-Type": "application/json"})
    r = c.getresponse(); body = r.read().decode("utf-8"); c.close()
    return r.status, body


# /role/{key} must NOT carry score fields
status, body = get("/role/" + key)
check("/role returns 200", status == 200)
d = json.loads(body)
check("/role omits fit", "fit" not in d)
check("/role omits band", "band" not in d)
check("/role omits screen", "screen" not in d)
check("/role includes JD link", d.get("jd_link", "").endswith("/jd.md") or d["jd_link"].startswith("http"))
check("/role includes extraction.gates", "gates" in d.get("extraction", {}))

# /score must be locked before any verdict
status, _ = get("/score/" + key)
check("/score locked before verdict (423)", status == 423)

# POST the verdict
status, body = post("/verdict", {"role_key": key, "verdict": "pursue",
                                  "reason": "frontier strategy + C-suite"})
check("POST /verdict returns 200", status == 200)
v = json.loads(body)
verdict_id = v.get("verdict_id", "")
check("verdict_id non-empty", bool(verdict_id))
check("ledger_row_num >= 1", v.get("ledger_row_num", 0) >= 1)

# Now /score must unlock with the verdict_id
status, body = get("/score/" + key + "?after=" + verdict_id)
check("/score 200 after verdict", status == 200)
score = json.loads(body)
check("/score returns fit", score.get("fit") == "88")
check("/score returns band", score.get("band") == "safety")

# Without the verdict_id it stays locked
status, _ = get("/score/" + key)
check("/score still locked without verdict_id", status == 423)

# Append-only: file count and that prior row is preserved
text = open(os.path.join(root, "calibration-ledger.md"), encoding="utf-8").read()
check("ledger row appended (key token present)", "key:" + key in text)

# Rubric-version change without ack -> 409
open(os.path.join(root, "reference", "fit-rubric.md"), "w", encoding="utf-8").write(
    "---\nrubric-version: 4\n---\n# rubric\n")
_seed(root, key="beta-bullseye")
status, _ = post("/verdict", {"role_key": "beta-bullseye", "verdict": "pursue",
                              "reason": "x"})
check("rubric changed mid-batch -> 409", status == 409)
status, _ = post("/verdict", {"role_key": "beta-bullseye", "verdict": "pursue",
                              "reason": "x", "ack_rubric_changed": True})
check("ack rubric change -> 200", status == 200)

# Snapshot is present in the appended log row
import json as _j
log = open(os.path.join(root, "calibration-log.jsonl"), encoding="utf-8").read().strip().splitlines()
last = _j.loads(log[-1])
check("log row carries extraction_snapshot", "extraction_snapshot" in last)
check("snapshot has gates", "gates" in last["extraction_snapshot"])
check("snapshot has variables", "variables" in last["extraction_snapshot"])

shutil.rmtree(root)
print()
print("FAILED:", fails if fails else "none")
raise SystemExit(1 if fails else 0)
