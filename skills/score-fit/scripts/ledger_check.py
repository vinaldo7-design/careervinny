#!/usr/bin/env python3
"""Executable calibration ledger — a regression guard.

Each calibration-ledger.md row that carries a human verdict AND an explicit
`key:<role-key>` (resolvable to a scored state/roles/<key>/score.md) becomes an
assertion: the machine screen/band must not contradict the human verdict by more than
ONE band. pursue↔reject = FAIL; pursue↔achievable = PASS. Run after EVERY engine or
rubric change — it must go red if an edit regresses an already-decided role.

Rows without a key (e.g. the legacy pre-machine verdicts) are reported PENDING and
skipped. A role the machine HELD (band null from a staleness/abstain, not a reject) is
also skipped — the machine didn't decide, so it can't contradict.

Python 3.8, stdlib only. Exit non-zero on any contradiction.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "..", "..")
LEDGER = os.path.join(REPO, "calibration-ledger.md")
ROLES_DIR = os.path.join(REPO, "state", "roles")

# A single ordinal "engage-ability" scale shared by both sides.
BAND_ORD = {"safety": 4, "achievable": 3, "stretch": 2, "moonshot": 1, "reject": 0}
VERDICT_ORD = {"pursue": 3, "on-ramp": 2, "no": 0}
TOLERANCE = 1  # contradiction = ordinal distance strictly greater than this


def verdict_ord(raw):
    """Normalise a ledger verdict cell to an ordinal. on-ramp wins over pursue when both
    words appear (e.g. 'on-ramp (pursue)')."""
    v = (raw or "").lower()
    if "on-ramp" in v or "on ramp" in v:
        return VERDICT_ORD["on-ramp"]
    if "pursue" in v:
        return VERDICT_ORD["pursue"]
    if re.search(r"\bno\b", v):
        return VERDICT_ORD["no"]
    return None


def _frontmatter(text, key):
    m = re.search(r"(?m)^%s:\s*(.+)$" % re.escape(key), text)
    return m.group(1).strip() if m else ""


def machine_ord(score_md_text):
    """(ordinal, label) from a score.md, or (None, 'held/abstain') if the machine did not
    decide (band null but not a reject — e.g. a stale role held for verification)."""
    screen = _frontmatter(score_md_text, "screen").lower()
    band_word = _frontmatter(score_md_text, "band").split()[0].strip().lower() if _frontmatter(score_md_text, "band") else ""
    if band_word in BAND_ORD and band_word != "reject":
        return BAND_ORD[band_word], band_word
    if screen == "reject":
        return 0, "reject"
    return None, "held/abstain"


def parse_ledger(path):
    """Yield (num, role_cell, verdict_cell, role_key|None) for each data row."""
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3 or not re.match(r"^\d+$", cells[0]):
            continue  # header / separator / prose
        role, verdict = cells[1], cells[2]
        m = re.search(r"key:([a-z0-9][a-z0-9-]+)", role)
        rows.append((cells[0], role, verdict, m.group(1) if m else None))
    return rows


def main():
    if not os.path.exists(LEDGER):
        print("no calibration-ledger.md — nothing to check")
        return 0
    rows = parse_ledger(LEDGER)
    checked, pending, failures = [], [], []
    for num, role, verdict, key in rows:
        vo = verdict_ord(verdict)
        if key is None or vo is None:
            pending.append((num, role, verdict, "no key" if key is None else "unparsed verdict"))
            continue
        sp = os.path.join(ROLES_DIR, key, "score.md")
        if not os.path.exists(sp):
            pending.append((num, role, verdict, "no score.md for key:%s" % key))
            continue
        mo, label = machine_ord(open(sp, encoding="utf-8").read())
        if mo is None:
            pending.append((num, role, verdict, "machine held (%s)" % label))
            continue
        dist = abs(vo - mo)
        rec = (num, role, verdict, label, dist)
        (failures if dist > TOLERANCE else checked).append(rec)

    print("=== calibration ledger regression check ===")
    for num, role, verdict, label, dist in checked:
        print("  PASS  #%s  verdict=%s  machine=%s  (dist %d)" % (num, verdict, label, dist))
    for num, role, verdict, label, dist in failures:
        print("  FAIL  #%s  %s — verdict=%s but machine=%s (dist %d > %d)"
              % (num, role.split("key:")[0].strip(" `"), verdict, label, dist, TOLERANCE))
    if pending:
        print("  --- pending (not machine-scored): %d ---" % len(pending))
        for num, role, verdict, why in pending:
            print("      #%s %s [%s]" % (num, role.split("key:")[0].strip(" `"), why))
    print("checked=%d  failures=%d  pending=%d" % (len(checked), len(failures), len(pending)))
    if failures:
        print("REGRESSION: an edit made the machine contradict an already-decided role.")
        return 1
    print("OK" + (" (guard armed — 0 decided+scored roles yet)" if not checked else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
