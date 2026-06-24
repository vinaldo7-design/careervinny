#!/usr/bin/env python3
"""Pure-function proposal engine.

Inputs: batch verdict rows, parsed rubric, decided-role context, past gate-fire counts.
Outputs: list of proposal-card dicts, each with reasoning and downstream re-band.

No I/O side effects — caller is responsible for reading rows/rubric and writing audit.
"""
import copy
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "score-fit", "scripts"))
try:
    import scorer as SC  # for hypothetical re-scoring
except Exception:
    SC = None

MAX_WEIGHT_MAGNITUDE = 3
DIVERGENCE_THRESHOLD = 3
GATE_PERFECT_PREDICTOR_MIN = 6
GATE_NOT_FIRED_BATCHES = 3


def _proposal_id(kind, var_id, magnitude, batch_id):
    s = "%s|%s|%s|%s" % (kind, var_id, magnitude, batch_id)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def _variable_verdict(row, var_id):
    return ((row.get("extraction_snapshot") or {}).get("variables") or {}).get(var_id, {}).get("verdict")


def _samples_for(rows, var_id, predicate_pair):
    """predicate_pair = (verdict_str, variable_verdict_str). Returns samples list."""
    v_required, ev_required = predicate_pair
    out = []
    for r in rows:
        if r.get("verdict") != v_required:
            continue
        if _variable_verdict(r, var_id) != ev_required:
            continue
        out.append({
            "role_key": r.get("role_key"),
            "your_verdict": v_required,
            "variable_verdict": ev_required,
        })
    return out[:6]


def _weight_proposals(rows, rubric, batch_id, decided_roles, repo_root):
    """Patterns:
        pursue@UNMET >= 3 on variable V -> weight-up V (rubric undervalued V)
        no@MET     >= 3 on variable V -> weight-down V (rubric over-valued V)
    """
    out = []
    var_ids = [r["id"] for r in rubric.get("rows", []) if r.get("kind") in ("spine", "heavy", "supporting")]
    for vid in var_ids:
        pu = sum(1 for r in rows if r.get("verdict") == "pursue" and _variable_verdict(r, vid) == "UNMET")
        nm = sum(1 for r in rows if r.get("verdict") == "no" and _variable_verdict(r, vid) == "MET")
        rubric_row = next((rr for rr in rubric["rows"] if rr["id"] == vid), None)
        current_w = rubric_row.get("weight") if rubric_row else None
        if pu >= DIVERGENCE_THRESHOLD:
            mag = min(pu, MAX_WEIGHT_MAGNITUDE)
            samples = _samples_for(rows, vid, ("pursue", "UNMET"))
            reasoning = (
                "You said pursue on %d roles where the extraction marked `%s` as UNMET. "
                "The rubric currently weights `%s` at %s. The pattern suggests `%s` may be under-weighted "
                "for the kinds of roles you want — your gut overrode the rubric's signal."
                % (pu, vid, vid, current_w, vid)
            )
            reband = _downstream_reband(decided_roles, rubric, [{"var_id": vid, "delta": +mag}], repo_root)
            out.append({
                "proposal_id": _proposal_id("weight-up", vid, mag, batch_id),
                "kind": "weight-up", "var_id": vid, "magnitude": mag,
                "confidence": "high", "reasoning": reasoning, "samples": samples,
                "current_weight": current_w, "proposed_weight": (current_w + mag) if isinstance(current_w, int) else None,
                "downstream_reband": reband,
            })
        if nm >= DIVERGENCE_THRESHOLD:
            mag = min(nm, MAX_WEIGHT_MAGNITUDE)
            samples = _samples_for(rows, vid, ("no", "MET"))
            reasoning = (
                "You said no on %d roles where the extraction marked `%s` as MET. "
                "The rubric currently weights `%s` at %s. The pattern suggests `%s` may be over-weighted "
                "or its how-to-read fires on a signal you don't actually value."
                % (nm, vid, vid, current_w, vid)
            )
            reband = _downstream_reband(decided_roles, rubric, [{"var_id": vid, "delta": -mag}], repo_root)
            out.append({
                "proposal_id": _proposal_id("weight-down", vid, mag, batch_id),
                "kind": "weight-down", "var_id": vid, "magnitude": mag,
                "confidence": "high", "reasoning": reasoning, "samples": samples,
                "current_weight": current_w, "proposed_weight": max(0, current_w - mag) if isinstance(current_w, int) else None,
                "downstream_reband": reband,
            })
    return out


def _gate_proposals(rows, rubric, batch_id, past_gate_fires):
    out = []
    # GATE-ADD: a non-gate variable that perfectly predicts in this batch
    non_gate_vars = [rr["id"] for rr in rubric.get("rows", []) if rr.get("kind") != "gate"]
    for vid in non_gate_vars:
        pursues_met = sum(1 for r in rows if r.get("verdict") == "pursue" and _variable_verdict(r, vid) == "MET")
        pursues_total = sum(1 for r in rows if r.get("verdict") == "pursue")
        nos_unmet = sum(1 for r in rows if r.get("verdict") == "no" and _variable_verdict(r, vid) == "UNMET")
        nos_total = sum(1 for r in rows if r.get("verdict") == "no")
        if pursues_total + nos_total < GATE_PERFECT_PREDICTOR_MIN:
            continue
        if pursues_met == pursues_total and nos_unmet == nos_total and pursues_total > 0 and nos_total > 0:
            reasoning = (
                "Across this batch, `%s` is a perfect predictor of your verdict: every pursue extracted "
                "MET (%d/%d) and every no extracted UNMET (%d/%d). %d roles total with no exceptions — "
                "this is the signature of a HARD gate, not a graded weight. "
                "Consider promoting `%s` from heavy variable to a gate. Gate promotion is a structural "
                "change (the audit will record your decision either way)."
                % (vid, pursues_met, pursues_total, nos_unmet, nos_total,
                   pursues_total + nos_total, vid)
            )
            samples = (_samples_for(rows, vid, ("pursue", "MET"))[:3]
                       + _samples_for(rows, vid, ("no", "UNMET"))[:3])
            out.append({
                "proposal_id": _proposal_id("gate-add", vid, 0, batch_id),
                "kind": "gate-add", "var_id": vid, "magnitude": 0,
                "confidence": "low", "reasoning": reasoning, "samples": samples,
                "current_weight": None, "proposed_weight": None,
                "downstream_reband": {"count": 0, "roles": []},
            })

    # GATE-REMOVE: existing gate that hasn't fired in N consecutive batches
    consecutive = (past_gate_fires or {}).get("_consecutive_zero_batches", {})
    gate_vars = [rr["id"] for rr in rubric.get("rows", []) if rr.get("kind") == "gate"]
    for gid in gate_vars:
        if consecutive.get(gid, 0) >= GATE_NOT_FIRED_BATCHES:
            reasoning = (
                "Gate `%s` has not fired in the last %d batches. Either the scout no longer surfaces "
                "roles that trigger it, or the gate is over-broad and effectively retired in practice. "
                "Removing a gate is a structural change — consider deferring if you expect to scout a "
                "new industry where this gate would matter."
                % (gid, consecutive.get(gid, 0))
            )
            out.append({
                "proposal_id": _proposal_id("gate-remove", gid, 0, batch_id),
                "kind": "gate-remove", "var_id": gid, "magnitude": 0,
                "confidence": "low", "reasoning": reasoning, "samples": [],
                "current_weight": 0, "proposed_weight": None,
                "downstream_reband": {"count": 0, "roles": []},
            })
    return out


def _downstream_reband(decided_roles, rubric, edits, repo_root):
    """For each decided role, recompute band under (rubric + edits) and report deltas.

    edits = [{"var_id": str, "delta": int}, ...] applied to weights.
    A decided role is a dict shaped: {role_key, score_md_band, extraction, jd_body?, ...}.
    If scorer cannot be imported (test mode), returns empty.
    """
    if SC is None or not decided_roles:
        return {"count": 0, "roles": []}
    hypothetical = copy.deepcopy(rubric)
    for e in edits:
        for row in hypothetical.get("rows", []):
            if row.get("id") == e["var_id"] and isinstance(row.get("weight"), int):
                row["weight"] = row["weight"] + e["delta"]
    changes = []
    for d in decided_roles:
        try:
            jd_body = d.get("jd_body", "")
            ext = d.get("extraction") or {}
            new = SC.score(ext, hypothetical, {"version": "1"}, jd_body, posting_days=None)
            new_band = new.get("band")
        except Exception:
            continue
        old_band = d.get("score_md_band")
        if new_band != old_band:
            changes.append({"role_key": d.get("role_key"),
                            "from_band": old_band, "to_band": new_band})
    return {"count": len(changes), "roles": changes[:10]}


def compute_proposals(rows, rubric, decided_roles=None, past_gate_fires=None, repo_root=None):
    """Top-level: combine weight + gate proposals for the given batch."""
    decided_roles = decided_roles or []
    past_gate_fires = past_gate_fires or {}
    batch_id = max((r.get("batch_id") or 0) for r in rows) if rows else 0
    return _weight_proposals(rows, rubric, batch_id, decided_roles, repo_root) + _gate_proposals(rows, rubric, batch_id, past_gate_fires)
