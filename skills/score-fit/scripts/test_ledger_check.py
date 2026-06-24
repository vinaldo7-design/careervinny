#!/usr/bin/env python3
"""Tests for the ledger regression guard's contradiction logic (no files, no network).
Proves the guard goes RED on a >1-band divergence and stays green within tolerance.
Run: python3 test_ledger_check.py"""
import ledger_check as L

fails = []
def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        fails.append(name)


def md(screen, band):
    return "screen: %s\nband: %s\n" % (screen, band)


def verdict_vs(verdict, screen, band):
    vo = L.verdict_ord(verdict)
    mo, _ = L.machine_ord(md(screen, band))
    if vo is None or mo is None:
        return "skip"
    return "fail" if abs(vo - mo) > L.TOLERANCE else "pass"


# --- verdict normalisation (on-ramp wins over pursue) ---
check("verdict pursue", L.verdict_ord("pursue (strong)") == 3)
check("verdict on-ramp wins over pursue", L.verdict_ord("on-ramp (pursue)") == 2)
check("verdict no", L.verdict_ord("no (hard)") == 0)

# --- machine_ord ---
check("machine achievable -> 3", L.machine_ord(md("flag", "achievable"))[0] == 3)
check("machine moonshot(provisional) -> 1", L.machine_ord(md("flag", "moonshot (provisional — odds low-confidence)"))[0] == 1)
check("machine reject -> 0", L.machine_ord(md("reject", "null"))[0] == 0)
check("machine held (flag + null) -> None (abstain)", L.machine_ord(md("flag", "null"))[0] is None)

# --- the user's two anchors ---
check("pursue ↔ reject = FAIL", verdict_vs("pursue (strong)", "reject", "null") == "fail")
check("pursue ↔ achievable = PASS", verdict_vs("pursue (strong)", "flag", "achievable") == "pass")

# --- more contradiction cases ---
check("pursue ↔ moonshot = FAIL (2 bands)", verdict_vs("pursue", "flag", "moonshot") == "fail")
check("pursue ↔ safety = PASS", verdict_vs("pursue", "pass", "safety") == "pass")
check("no ↔ reject = PASS", verdict_vs("no (hard)", "reject", "null") == "pass")
check("no ↔ moonshot = PASS (1 band)", verdict_vs("no", "flag", "moonshot") == "pass")
check("no ↔ safety = FAIL", verdict_vs("no", "pass", "safety") == "fail")
check("on-ramp ↔ achievable = PASS", verdict_vs("on-ramp", "flag", "achievable") == "pass")
check("on-ramp ↔ reject = FAIL", verdict_vs("on-ramp", "reject", "null") == "fail")

# --- a HELD (stale) role is skipped, never a contradiction ---
check("held role is skipped", verdict_vs("pursue", "flag", "null") == "skip")

print()
print("FAILED:", fails if fails else "none")
raise SystemExit(1 if fails else 0)
