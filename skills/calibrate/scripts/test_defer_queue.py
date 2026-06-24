#!/usr/bin/env python3
import os, tempfile, shutil
import defer_queue as DQ

fails = []
def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        fails.append(name)


root = tempfile.mkdtemp(prefix="dq-")
try:
    check("empty: no deferred", DQ.currently_deferred(root) == [])

    DQ.record_event(root, "p1", "deferred", batch_id=1, payload={"kind": "weight-up", "var_id": "client-facing"})
    DQ.record_event(root, "p2", "deferred", batch_id=1, payload={"kind": "gate-add", "var_id": "intellectual-agency"})
    deferred = DQ.currently_deferred(root)
    check("two deferred", len(deferred) == 2)
    check("payload survives", any(d["payload"].get("var_id") == "client-facing" for d in deferred))

    # Accept one -> it drops from deferred
    DQ.record_event(root, "p1", "accepted", batch_id=2)
    deferred = DQ.currently_deferred(root)
    check("after accept: 1 deferred", len(deferred) == 1)
    check("the right one is still deferred", deferred[0]["proposal_id"] == "p2")

    # Defer again (no-op should be safe)
    DQ.record_event(root, "p2", "deferred", batch_id=2, payload={"kind": "gate-add", "var_id": "intellectual-agency"})
    check("re-deferring same id stays deferred", any(d["proposal_id"] == "p2" for d in DQ.currently_deferred(root)))

    # Reject -> drops
    DQ.record_event(root, "p2", "rejected", batch_id=3)
    check("after reject: 0 deferred", len(DQ.currently_deferred(root)) == 0)

    # File is append-only — verify by reading every event
    log_path = os.path.join(root, "state", "batches", "proposal-events.jsonl")
    n_events = sum(1 for _ in open(log_path))
    check("all events persisted (append-only)", n_events == 5)
finally:
    shutil.rmtree(root)

print()
print("FAILED:", fails if fails else "none")
raise SystemExit(1 if fails else 0)
