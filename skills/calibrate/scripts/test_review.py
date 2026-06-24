#!/usr/bin/env python3
import json
import review as R

fails = []
def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        fails.append(name)


# 4 divergences on client-facing — verdict pursue but UNMET in extraction.
rows = []
for i, k in enumerate(["roleA", "roleB", "roleC", "roleD"]):
    rows.append({
        "role_key": k, "verdict": "pursue", "reason": "client-facing matters here",
        "rubric_version": "3", "machine_band": "stretch", "machine_screen": "flag",
        "extraction_snapshot": {"variables": {"client-facing": {"verdict": "UNMET"}}}})
# One opposite pattern: no on a MET frontier-strategy
rows.append({"role_key": "roleE", "verdict": "no", "reason": "boring even with frontier",
             "rubric_version": "3", "machine_band": "safety", "machine_screen": "pass",
             "extraction_snapshot": {"variables": {"frontier-strategy": {"verdict": "MET"}}}})

summary = R.summarise(rows)
check("total count 5", summary["count"] == 5)
cf = summary["by_variable"].get("client-facing", {})
check("client-facing pursue_at_unmet >= 4", cf.get("pursue_at_unmet", 0) >= 4)
fr = summary["by_variable"].get("frontier-strategy", {})
check("frontier-strategy no_at_met >= 1", fr.get("no_at_met", 0) >= 1)

deltas = R.propose_deltas(summary, rubric_version="3")
text = "\n".join(deltas)
check("a delta names client-facing", "client-facing" in text)
check("each delta is status: proposed", text.count("status: proposed") == len(deltas))
check("no delta proposes a gate change autonomously", "kind: gate" not in text)

print()
print("FAILED:", fails if fails else "none")
raise SystemExit(1 if fails else 0)
