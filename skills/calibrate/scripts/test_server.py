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
            "---\nrubric-version: 3\n---\n# rubric\n\n"
            "| id | variable | kind | weight | floor | how |\n"
            "|----|----------|------|--------|-------|-----|\n"
            "| frontier-strategy | Frontier strategy | spine | 10 | — | AI strategy mention |\n"
        )
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
    "---\nrubric-version: 4\n---\n# rubric\n\n"
    "| id | variable | kind | weight | floor | how |\n"
    "|----|----------|------|--------|-------|-----|\n"
    "| frontier-strategy | Frontier strategy | spine | 10 | — | AI strategy mention |\n"
)
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

# Regression: __QUEUE_JSON__ embedded in the HTML index MUST NOT carry score fields.
status, body = get("/")
check("/ returns 200", status == 200)
import re as _re
m = _re.search(r"window\.__QUEUE__\s*=\s*(\[.*?\]);", body, _re.S)
check("__QUEUE__ assignment found in HTML", m is not None)
if m:
    queue_text = m.group(1)
    check("queue JSON does not leak 'fit'", '"fit"' not in queue_text)
    check("queue JSON does not leak 'band'", '"band"' not in queue_text)
    check("queue JSON does not leak 'screen'", '"screen"' not in queue_text)
    check("queue JSON does not leak 'odds'", '"odds"' not in queue_text)

# /batch-summary returns 200 with expected keys
status, body = get("/batch-summary")
check("/batch-summary returns 200", status == 200)
bs = json.loads(body)
check("/batch-summary has count", "count" in bs)
check("/batch-summary has verdict_mix", "verdict_mix" in bs)
check("/batch-summary has by_industry", "by_industry" in bs)
check("/batch-summary has machine_fit_by_verdict", "machine_fit_by_verdict" in bs)
check("/batch-summary has divergences", "divergences" in bs)
check("/batch-summary has proposed_deltas_summary", "proposed_deltas_summary" in bs)
check("/batch-summary count >= 2", bs.get("count", 0) >= 2)
check("/batch-summary verdict_mix pursue >= 2", bs["verdict_mix"].get("pursue", 0) >= 2)

# Default window is last 20 rows (current-batch semantics)
status, body = get("/batch-summary")
data = json.loads(body)
check("/batch-summary default window count <= 20", data["count"] <= 20)
# ?window=all returns lifetime
status_all, body_all = get("/batch-summary?window=all")
data_all = json.loads(body_all)
check("/batch-summary ?window=all count >= default count", data_all["count"] >= data["count"])
# Invalid window -> 400
status_bad, _ = get("/batch-summary?window=banana")
check("/batch-summary invalid window -> 400", status_bad == 400)

# /batch/current
status, body = get("/batch/current")
check("/batch/current returns 200", status == 200)
bc = json.loads(body)
check("/batch/current has batch_id", isinstance(bc.get("batch_id"), int))
check("/batch/current has verdicts_in_batch", "verdicts_in_batch" in bc)
check("verdicts_in_batch counts existing rows for current batch", bc["verdicts_in_batch"] >= 1)

# /queue/preview — seed a never-verdicted role so prev["roles"] is non-empty
_seed(root, key="gamma-unvoted")
status, body = get("/queue/preview")
check("/queue/preview 200", status == 200)
prev = json.loads(body)
check("/queue/preview has n_roles", "n_roles" in prev)
check("/queue/preview roles non-empty (gamma-unvoted present)", len(prev.get("roles", [])) >= 1)
r0 = prev["roles"][0]
check("/queue/preview omits fit", "fit" not in r0)
check("/queue/preview omits band", "band" not in r0)
check("/queue/preview omits screen", "screen" not in r0)

# /batch/propose with force
status, body = post("/batch/propose", {"force": True, "force_reason": "fixture"})
check("/batch/propose 200 with force", status == 200)
prop = json.loads(body)
check("/batch/propose has cards list", isinstance(prop.get("cards"), list))
check("/batch/propose has deferred list", isinstance(prop.get("deferred"), list))
check("/batch/propose has verdict_mix", isinstance(prop.get("verdict_mix"), dict))

# /batch/apply round-trip: proposal_id end-to-end
# Install a stub check.sh that always exits 0 so apply_proposals can commit weight changes.
stub_dir = os.path.join(root, "skills", "score-fit", "scripts")
os.makedirs(stub_dir, exist_ok=True)
stub_sh = os.path.join(stub_dir, "check.sh")
open(stub_sh, "w").write("#!/usr/bin/env bash\nexit 0\n")
os.chmod(stub_sh, 0o755)

# Seed 3 extra pursue roles with frontier-strategy UNMET to trigger a weight-up proposal.
for idx in range(3):
    rk = "delta-pursue-%d" % idx
    d = os.path.join(root, "state", "roles", rk)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "jd.md"), "w").write(
        "---\ncompany: Delta\ntitle: Mgr %d\nlocation: London\n"
        "posting-age: 1 days\nsource-url: https://example.com/%d\n---\nJD\n" % (idx, idx))
    open(os.path.join(d, "extraction.json"), "w").write(json.dumps({
        "gates": {"visa-sponsorship": "pass"},
        "variables": {"frontier-strategy": {"verdict": "UNMET", "quote": ""}}}))
    open(os.path.join(d, "score.md"), "w").write(
        "---\nrubric-version: 4\nfit: 50\nband: safety\nscreen: pass\n---\nBODY\n")
    # Write a JSONL row directly into the log for the current batch
    import time as _time
    current_bid = S.B.current_batch_id(root)
    row = {
        "ts": _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime()),
        "role_key": rk,
        "verdict": "pursue",
        "reason": "round-trip test",
        "rubric_version": "4",
        "batch_id": current_bid,
        "extraction_snapshot": {
            "gates": {"visa-sponsorship": "pass"},
            "variables": {"frontier-strategy": {"verdict": "UNMET", "quote": ""}},
        },
    }
    with open(os.path.join(root, "calibration-log.jsonl"), "a") as fh:
        fh.write(json.dumps(row) + "\n")

# Call /batch/propose with force to get proposal cards.
status_rt, body_rt = post("/batch/propose", {"force": True, "force_reason": "round-trip test"})
check("/batch/apply round-trip: propose returns 200", status_rt == 200)
prop_rt = json.loads(body_rt)
weight_cards = [c for c in prop_rt.get("cards", []) if c.get("kind") == "weight-up"]
check("/batch/apply round-trip: at least one weight-up card", len(weight_cards) >= 1)

if weight_cards:
    pid = weight_cards[0]["proposal_id"]
    var_id = weight_cards[0]["var_id"]
    old_weight = weight_cards[0].get("current_weight")

    # Read rubric weight before apply.
    rubric_text_before = open(os.path.join(root, "reference", "fit-rubric.md"), encoding="utf-8").read()

    # Call /batch/apply with the proposal_id.
    status_ap, body_ap = post("/batch/apply", {"accept_ids": [pid], "reject_ids": [], "defer_ids": []})
    check("/batch/apply round-trip: apply returns 200", status_ap == 200)
    ap_result = json.loads(body_ap)
    check("/batch/apply round-trip: applied list contains proposal_id",
          any(a.get("proposal_id") == pid for a in ap_result.get("applied", [])))

    # Rubric file must reflect the weight change (weight-up means new > old).
    rubric_text_after = open(os.path.join(root, "reference", "fit-rubric.md"), encoding="utf-8").read()
    check("/batch/apply round-trip: rubric file changed after apply", rubric_text_after != rubric_text_before)

# /batch/propose without force on empty batch -> 409
# (advance to a new empty batch first by accepting nothing — only if we haven't already advanced above)
if not weight_cards:
    status_e, body_e = post("/batch/apply", {"accept_ids": [], "reject_ids": [], "defer_ids": []})
    check("/batch/apply with empty accept advances counter (no-op path)", status_e == 200)
status_409, _ = post("/batch/propose", {})
check("/batch/propose empty batch without force -> 409", status_409 == 409)

shutil.rmtree(root)
print()
print("FAILED:", fails if fails else "none")
raise SystemExit(1 if fails else 0)
