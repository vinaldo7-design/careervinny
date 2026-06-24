#!/usr/bin/env python3
"""Tests for proposals.py — weight proposals, gate proposals, reasoning, re-band."""
import json, os, shutil, tempfile
import proposals as P

fails = []
def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        fails.append(name)


# Minimal rubric fixture: 2 spine, 1 heavy variable
RUBRIC = {
    "version": "3",
    "rows": [
        {"id": "frontier-strategy", "kind": "spine", "weight": 30, "floor": 0.4},
        {"id": "mgmt-ladder", "kind": "spine", "weight": 20, "floor": 0.4},
        {"id": "client-facing", "kind": "heavy", "weight": 10, "floor": None},
        {"id": "visa-sponsorship", "kind": "gate", "weight": 0, "floor": None},
        {"id": "disq-pure-sales", "kind": "gate", "weight": 0, "floor": None},
    ],
    "comp_curve": [],
}

# 4 rows: pursue@UNMET on client-facing — should trigger weight-down (no@MET = 0)
ROWS_WEIGHT = [
    {"role_key": "a", "verdict": "pursue", "batch_id": 1, "rubric_version": "3",
     "extraction_snapshot": {"variables": {"client-facing": {"verdict": "UNMET", "quote": ""},
                                           "frontier-strategy": {"verdict": "MET", "quote": "x"}}}},
    {"role_key": "b", "verdict": "pursue", "batch_id": 1, "rubric_version": "3",
     "extraction_snapshot": {"variables": {"client-facing": {"verdict": "UNMET", "quote": ""}}}},
    {"role_key": "c", "verdict": "pursue", "batch_id": 1, "rubric_version": "3",
     "extraction_snapshot": {"variables": {"client-facing": {"verdict": "UNMET", "quote": ""}}}},
    {"role_key": "d", "verdict": "pursue", "batch_id": 1, "rubric_version": "3",
     "extraction_snapshot": {"variables": {"client-facing": {"verdict": "UNMET", "quote": ""}}}},
]
proposals = P.compute_proposals(ROWS_WEIGHT, RUBRIC, decided_roles=[], past_gate_fires={"disq-pure-sales": 5}, repo_root="/tmp/np")
check("4 pursue@UNMET produces a client-facing weight-up proposal (gut said yes, rubric undervalued)",
      any(pr["kind"] == "weight-up" and pr["var_id"] == "client-facing" for pr in proposals))
weight_card = [pr for pr in proposals if pr["kind"] == "weight-up" and pr["var_id"] == "client-facing"][0]
check("magnitude capped at 3", weight_card["magnitude"] == 3)
check("reasoning mentions UNMET", "UNMET" in weight_card["reasoning"])
check("reasoning mentions sample count", "4" in weight_card["reasoning"])
check("samples has 4 entries", len(weight_card["samples"]) == 4)
check("samples carry role_key + verdicts", weight_card["samples"][0].get("role_key") == "a" and weight_card["samples"][0].get("your_verdict") == "pursue")
check("confidence high for weight proposal", weight_card["confidence"] == "high")
check("proposal_id is stable hex", isinstance(weight_card["proposal_id"], str) and len(weight_card["proposal_id"]) >= 8)

# Re-running yields the same id
prop2 = P.compute_proposals(ROWS_WEIGHT, RUBRIC, decided_roles=[], past_gate_fires={"disq-pure-sales": 5}, repo_root="/tmp/np")
ids1 = sorted(pr["proposal_id"] for pr in proposals)
ids2 = sorted(pr["proposal_id"] for pr in prop2)
check("proposal_ids stable across re-computation", ids1 == ids2)


# GATE-ADD: every pursue extracts intellectual-agency MET, every no extracts UNMET — perfect predictor
ROWS_GATE = []
for k in ("p1","p2","p3","p4","p5","p6","p7"):
    ROWS_GATE.append({"role_key": k, "verdict": "pursue", "batch_id": 1, "rubric_version": "3",
                      "extraction_snapshot": {"variables": {"intellectual-agency": {"verdict": "MET", "quote": "x"}}}})
for k in ("n1","n2","n3","n4","n5","n6","n7"):
    ROWS_GATE.append({"role_key": k, "verdict": "no", "batch_id": 1, "rubric_version": "3",
                      "extraction_snapshot": {"variables": {"intellectual-agency": {"verdict": "UNMET", "quote": ""}}}})

RUBRIC_PLUS_IA = {**RUBRIC, "rows": RUBRIC["rows"] + [
    {"id": "intellectual-agency", "kind": "heavy", "weight": 12, "floor": None}]}
gate_props = P.compute_proposals(ROWS_GATE, RUBRIC_PLUS_IA, decided_roles=[], past_gate_fires={}, repo_root="/tmp/np")
ga = [pr for pr in gate_props if pr["kind"] == "gate-add" and pr["var_id"] == "intellectual-agency"]
check("perfect predictor triggers gate-add proposal", len(ga) == 1)
check("gate-add confidence is low", ga[0]["confidence"] == "low")
check("gate-add reasoning mentions perfect predictor", "perfect" in ga[0]["reasoning"].lower() or "predictor" in ga[0]["reasoning"].lower())


# GATE-REMOVE: gate disq-pure-sales has 0 fires in past 3 batches -> proposal
gate_rm_props = P.compute_proposals([], RUBRIC, decided_roles=[],
                                    past_gate_fires={"disq-pure-sales": 0,
                                                     "_consecutive_zero_batches": {"disq-pure-sales": 3}},
                                    repo_root="/tmp/np")
gr = [pr for pr in gate_rm_props if pr["kind"] == "gate-remove" and pr["var_id"] == "disq-pure-sales"]
check("3-batch zero-fire triggers gate-remove proposal", len(gr) == 1)


# DOWNSTREAM RE-BAND: a decided role with a known band re-bands if the weight changes
decided = [{
    "role_key": "old-1",
    "verdict": "pursue",
    "machine_band": "achievable",
    "score_md_band": "achievable",  # current band
    "extraction": {"variables": {
        "frontier-strategy": {"verdict": "MET"},
        "mgmt-ladder": {"verdict": "MET"},
        "client-facing": {"verdict": "UNMET"},
    }, "gates": {}, "penalties": {}, "comp": {"stated_gbp": None}, "multipliers": {}},
}]
# For now: just assert the field exists; precise band recomputation depends on
# wiring scorer.score in proposals.py — see Step 3.
props_with_reband = P.compute_proposals(ROWS_WEIGHT, RUBRIC, decided_roles=decided, past_gate_fires={}, repo_root="/tmp/np")
card_with_reband = [pr for pr in props_with_reband if pr["kind"] == "weight-up" and pr["var_id"] == "client-facing"][0]
check("downstream_reband field present", "downstream_reband" in card_with_reband)
check("downstream_reband has count", "count" in card_with_reband["downstream_reband"])
check("downstream_reband has roles list", isinstance(card_with_reband["downstream_reband"]["roles"], list))


# Stability: a proposal that doesn't cross threshold isn't emitted
ROWS_LOW = ROWS_WEIGHT[:2]  # only 2 pursue@UNMET -> below threshold of 3
proposals_low = P.compute_proposals(ROWS_LOW, RUBRIC, decided_roles=[], past_gate_fires={}, repo_root="/tmp/np")
check("below-threshold signal produces no weight proposal",
      not any(pr["kind"] == "weight-up" and pr["var_id"] == "client-facing" for pr in proposals_low))


print()
print("FAILED:", fails if fails else "none")
raise SystemExit(1 if fails else 0)
