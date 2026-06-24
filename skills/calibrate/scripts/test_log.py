#!/usr/bin/env python3
"""Tests for log.py — append-only writers and ledger row formatting."""
import json, os, tempfile, shutil
import log as L

fails = []
def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        fails.append(name)


def setup_repo():
    root = tempfile.mkdtemp(prefix="cal-log-")
    open(os.path.join(root, "calibration-log.jsonl"), "w").close()
    # Minimal ledger with one header + one separator + one prior row to count.
    open(os.path.join(root, "calibration-ledger.md"), "w", encoding="utf-8").write(
        "# Ledger\n\n"
        "| # | role | verdict | why | rubric band | GAP |\n"
        "|---|------|---------|-----|-------------|-----|\n"
        "| 1 | OldCo — Old Role | pursue | seed | high | match |\n"
    )
    return root


# format_ledger_row
role = {"key": "lloyds-strategy-director-cib", "company": "Lloyds", "title": "Strategy Director CIB"}
line = L.format_ledger_row(2, role, "pursue", "frontier AI + C-suite at a stable bank",
                           rubric_version="3")
check("ledger row starts with the row number", line.startswith("| 2 |"))
check("ledger row carries key token", "key:lloyds-strategy-director-cib" in line)
check("ledger row records verdict literally", "| pursue |" in line)
check("ledger row carries rubric-version", "rubric:3" in line)
check("ledger row ends with newline", line.endswith("\n"))

# append + count
root = setup_repo()
check("count starts at 1", L.count_ledger_rows(root) == 1)
n = L.append_ledger(root, line)
check("append returns new count == 2", n == 2)
text = open(os.path.join(root, "calibration-ledger.md"), encoding="utf-8").read()
check("ledger now contains the new row", "key:lloyds-strategy-director-cib" in text)
check("ledger original row preserved (append-only)", "OldCo — Old Role" in text)

# append_log
row = {"role_key": "lloyds-strategy-director-cib", "verdict": "pursue", "reason": "ok",
       "rubric_version": "3", "machine_fit": 80, "machine_band": "achievable",
       "ts": "2026-06-24T12:00:00Z"}
L.append_log(root, row)
L.append_log(root, dict(row, verdict="on-ramp"))
lines = open(os.path.join(root, "calibration-log.jsonl"), encoding="utf-8").read().strip().splitlines()
check("log file has exactly 2 lines after 2 appends", len(lines) == 2)
parsed = [json.loads(x) for x in lines]
check("log rows are valid JSON", all("role_key" in p for p in parsed))
check("log preserves verdict order", [p["verdict"] for p in parsed] == ["pursue", "on-ramp"])

shutil.rmtree(root)
print()
print("FAILED:", fails if fails else "none")
raise SystemExit(1 if fails else 0)
