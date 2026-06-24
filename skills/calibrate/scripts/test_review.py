#!/usr/bin/env python3
import json
import os
import tempfile
import review as R

fails = []
def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        fails.append(name)


# ---------------------------------------------------------------------------
# Existing tests — summarise / propose_deltas
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# NEW: batch_summary tests
# ---------------------------------------------------------------------------

def _make_row(role_key, verdict, machine_fit=None, machine_band="stretch",
              machine_screen="flag", industry=None, variables=None):
    row = {
        "role_key": role_key,
        "verdict": verdict,
        "reason": "test",
        "rubric_version": "3",
        "machine_band": machine_band,
        "machine_screen": machine_screen,
        "machine_fit": machine_fit,
        "extraction_snapshot": {"variables": variables or {}},
    }
    if industry is not None:
        row["industry"] = industry
    return row


# ── Test 1: batch_summary with 5 mixed-verdict rows returns correct counts ─
mixed_rows = [
    _make_row("r1", "pursue"),
    _make_row("r2", "pursue"),
    _make_row("r3", "on-ramp"),
    _make_row("r4", "no"),
    _make_row("r5", "no"),
]
bs = R.batch_summary(mixed_rows)
check("bs count == 5", bs["count"] == 5)
check("bs verdict_mix pursue == 2", bs["verdict_mix"]["pursue"] == 2)
check("bs verdict_mix on-ramp == 1", bs["verdict_mix"]["on-ramp"] == 1)
check("bs verdict_mix no == 2", bs["verdict_mix"]["no"] == 2)


# ── Test 2: by_industry bucketing (tempdir with jd.md fixtures) ──────────
with tempfile.TemporaryDirectory() as tmpdir:
    for rk, domain in [("rx1", "pharma:ml-research"), ("rx2", "pharma:strategy"),
                       ("rx3", "tech:product")]:
        role_dir = os.path.join(tmpdir, "state", "roles", rk)
        os.makedirs(role_dir)
        with open(os.path.join(role_dir, "jd.md"), "w") as fh:
            fh.write("---\ndomain: %s\n---\n" % domain)
    ind_rows = [
        _make_row("rx1", "pursue"),
        _make_row("rx2", "no"),
        _make_row("rx3", "on-ramp"),
    ]
    bs2 = R.batch_summary(ind_rows, repo_root=tmpdir)
    check("by_industry has pharma", "pharma" in bs2["by_industry"])
    check("by_industry pharma count == 2", bs2["by_industry"]["pharma"]["count"] == 2)
    check("by_industry has tech", "tech" in bs2["by_industry"])
    check("by_industry tech count == 1", bs2["by_industry"]["tech"]["count"] == 1)


# ── Test 3: machine_fit_by_verdict computes mean correctly ────────────────
fit_rows = [
    _make_row("f1", "pursue", machine_fit="70"),
    _make_row("f2", "pursue", machine_fit="80"),
    _make_row("f3", "no", machine_fit="40"),
]
bs3 = R.batch_summary(fit_rows)
pursue_stats = bs3["machine_fit_by_verdict"]["pursue"]
check("pursue mean == 75.0", pursue_stats["mean"] == 75.0)
check("pursue n == 2", pursue_stats["n"] == 2)
check("pursue min == 70", pursue_stats["min"] == 70)
check("pursue max == 80", pursue_stats["max"] == 80)
no_stats = bs3["machine_fit_by_verdict"]["no"]
check("no mean == 40.0", no_stats["mean"] == 40.0)


# ── Test 4: rows without machine_fit are skipped (no crash) ───────────────
null_fit_rows = [
    _make_row("n1", "pursue", machine_fit=None),
    _make_row("n2", "pursue", machine_fit="bad-value"),
    _make_row("n3", "on-ramp", machine_fit=""),
]
bs4 = R.batch_summary(null_fit_rows)
check("null-fit pursue n == 0", bs4["machine_fit_by_verdict"]["pursue"]["n"] == 0)
check("null-fit pursue mean == None", bs4["machine_fit_by_verdict"]["pursue"]["mean"] is None)
check("null-fit on-ramp n == 0", bs4["machine_fit_by_verdict"]["on-ramp"]["n"] == 0)


# ── Test 5: proposed_deltas_summary emits weight-up only at threshold ─────
# Need DIVERGENCE_THRESHOLD rows with pursue + UNMET for the same variable.
thresh = R.DIVERGENCE_THRESHOLD
below_thresh_rows = [_make_row("bt%d" % i, "pursue",
    variables={"my-var": {"verdict": "UNMET"}}) for i in range(thresh - 1)]
bs5a = R.batch_summary(below_thresh_rows)
weight_up_count = sum(1 for e in bs5a["proposed_deltas_summary"] if e["kind"] == "weight-up")
check("below-threshold: no weight-up entries", weight_up_count == 0)

at_thresh_rows = [_make_row("at%d" % i, "pursue",
    variables={"my-var": {"verdict": "UNMET"}}) for i in range(thresh)]
bs5b = R.batch_summary(at_thresh_rows)
wu_entries = [e for e in bs5b["proposed_deltas_summary"] if e["kind"] == "weight-up" and e["variable"] == "my-var"]
check("at-threshold: one weight-up entry for my-var", len(wu_entries) == 1)
check("at-threshold: count == threshold", wu_entries[0]["count"] == thresh)
check("at-threshold: sample_roles <= 6", len(wu_entries[0]["sample_roles"]) <= 6)


print()
print("FAILED:", fails if fails else "none")
raise SystemExit(1 if fails else 0)
