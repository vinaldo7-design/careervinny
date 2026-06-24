#!/usr/bin/env python3
"""Atomic apply: edit weights for accepted proposals, run guard, revert on red.

Gate accepts are NOT auto-applied to the rubric (structural changes are recorded
in gate_decisions and surfaced to the user via the audit modal for manual edit).
"""
import os
import re
import subprocess


_ROW_RE = re.compile(
    r'^(\|\s*(?P<id>[a-z0-9][a-z0-9-]+)\s*\|[^|]+\|[^|]+\|\s*)(?P<w>-?\d+)(\s*\|[^\n]*)$',
    re.MULTILINE,
)


def update_weight(text, var_id, new_weight):
    def _sub(m):
        if m.group("id") != var_id:
            return m.group(0)
        return m.group(1) + str(int(new_weight)) + m.group(4)
    return _ROW_RE.sub(_sub, text)


def _read_weight(text, var_id):
    for m in _ROW_RE.finditer(text):
        if m.group("id") == var_id:
            return int(m.group("w"))
    return None


def _parse_contradictions(stdout):
    out = []
    for line in (stdout or "").splitlines():
        m = re.search(r'(?:FAIL|contradiction)[^a-z0-9]*([a-z0-9][a-z0-9-]+)', line)
        if m:
            out.append(m.group(1))
    return out


def apply(accepted, rubric_path, check_cmd):
    """accepted: list of proposal dicts with kind/var_id/magnitude.

    Weight changes are applied. Gate-add / gate-remove accepts are recorded in
    gate_decisions for the audit but do NOT modify the rubric (gate add/remove is
    a structural change the user makes by hand or in a follow-up tool).
    """
    if not os.path.exists(rubric_path):
        return {"status": "no-op", "applied": [], "skipped": [], "contradicting_roles": [],
                "gate_decisions": [], "guard_output": "no rubric file"}

    with open(rubric_path, encoding="utf-8") as fh:
        before = fh.read()

    text = before
    applied = []
    skipped = []
    gate_decisions = []
    for p in accepted:
        kind = p.get("kind")
        if kind in ("gate-add", "gate-remove"):
            gate_decisions.append(p)
            continue
        if kind not in ("weight-up", "weight-down"):
            skipped.append({**p, "reason": "unknown kind"})
            continue
        direction = 1 if kind == "weight-up" else -1
        current = _read_weight(text, p["var_id"])
        if current is None:
            skipped.append({**p, "reason": "variable not found in rubric"})
            continue
        new = current + direction * int(p.get("magnitude", 0))
        text = update_weight(text, p["var_id"], new)
        applied.append({**p, "old_weight": current, "new_weight": new})

    if text == before:
        # Only gate decisions or nothing — no edit, no guard run.
        return {"status": "no-op", "applied": [], "skipped": skipped,
                "contradicting_roles": [], "gate_decisions": gate_decisions,
                "guard_output": "no weight edits"}

    with open(rubric_path, "w", encoding="utf-8") as fh:
        fh.write(text)

    proc = subprocess.run([check_cmd], capture_output=True, text=True)
    guard_output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        with open(rubric_path, "w", encoding="utf-8") as fh:
            fh.write(before)
        return {"status": "reverted", "applied": [], "skipped": skipped,
                "contradicting_roles": _parse_contradictions(guard_output),
                "gate_decisions": gate_decisions, "guard_output": guard_output}

    return {"status": "applied", "applied": applied, "skipped": skipped,
            "contradicting_roles": [], "gate_decisions": gate_decisions,
            "guard_output": guard_output}
