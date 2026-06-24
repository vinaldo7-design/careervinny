#!/usr/bin/env python3
import json, os, shutil, tempfile
import apply_proposals as A

fails = []
def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        fails.append(name)


rubric = (
    "---\nrubric-version: 3\n---\n\n"
    "| id | variable | kind | weight | floor | how-to-read |\n"
    "|----|----------|------|--------|-------|-------------|\n"
    "| frontier-strategy | Frontier strategy | spine | 30 | 0.4 | ... |\n"
    "| client-facing | Client facing | heavy | 10 | — | ... |\n"
)

# update_weight in isolation
new = A.update_weight(rubric, "client-facing", 13)
check("update_weight bumps client-facing to 13", "| client-facing | Client facing | heavy | 13 |" in new)


# apply: GREEN
root = tempfile.mkdtemp(prefix="ap-")
try:
    os.makedirs(os.path.join(root, "reference"))
    rp = os.path.join(root, "reference", "fit-rubric.md")
    open(rp, "w").write(rubric)
    check_sh = os.path.join(root, "check.sh")
    open(check_sh, "w").write("#!/bin/sh\nexit 0\n"); os.chmod(check_sh, 0o755)
    accepted = [
        {"proposal_id": "p1", "kind": "weight-up", "var_id": "client-facing", "magnitude": 3},
        {"proposal_id": "p2", "kind": "weight-down", "var_id": "frontier-strategy", "magnitude": 2},
    ]
    res = A.apply(accepted, rp, check_sh)
    check("green: status applied", res["status"] == "applied")
    check("green: 2 applied", len(res["applied"]) == 2)
    body_after = open(rp).read()
    check("green: client-facing now 13", "| client-facing | Client facing | heavy | 13 |" in body_after)
    check("green: frontier-strategy now 28", "| frontier-strategy | Frontier strategy | spine | 28 |" in body_after)
finally:
    shutil.rmtree(root)


# apply: RED -> revert
root = tempfile.mkdtemp(prefix="ap-")
try:
    os.makedirs(os.path.join(root, "reference"))
    rp = os.path.join(root, "reference", "fit-rubric.md")
    open(rp, "w").write(rubric)
    check_sh = os.path.join(root, "check.sh")
    open(check_sh, "w").write("#!/bin/sh\necho 'FAIL accenture-data-ai-strategy-manager: contradicting'\nexit 1\n"); os.chmod(check_sh, 0o755)
    accepted = [{"proposal_id": "p1", "kind": "weight-up", "var_id": "client-facing", "magnitude": 3}]
    res = A.apply(accepted, rp, check_sh)
    check("red: status reverted", res["status"] == "reverted")
    check("red: applied empty", res["applied"] == [])
    check("red: rubric unchanged", open(rp).read() == rubric)
    check("red: contradicting roles surfaced",
          any("accenture" in r for r in res["contradicting_roles"]))
finally:
    shutil.rmtree(root)


# Gate accepts surface as gate_decisions but do NOT edit the rubric
root = tempfile.mkdtemp(prefix="ap-")
try:
    os.makedirs(os.path.join(root, "reference"))
    rp = os.path.join(root, "reference", "fit-rubric.md")
    open(rp, "w").write(rubric)
    check_sh = os.path.join(root, "check.sh"); open(check_sh, "w").write("#!/bin/sh\nexit 0\n"); os.chmod(check_sh, 0o755)
    accepted = [{"proposal_id": "g1", "kind": "gate-add", "var_id": "intellectual-agency", "magnitude": 0}]
    res = A.apply(accepted, rp, check_sh)
    check("gate accept: status no-op (rubric not edited)", res["status"] == "no-op")
    check("gate accept: gate_decisions records it",
          "gate_decisions" in res and any(g["proposal_id"] == "g1" for g in res["gate_decisions"]))
    check("gate accept: rubric unchanged", open(rp).read() == rubric)
finally:
    shutil.rmtree(root)


print()
print("FAILED:", fails if fails else "none")
raise SystemExit(1 if fails else 0)
