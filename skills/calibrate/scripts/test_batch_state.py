#!/usr/bin/env python3
import os, tempfile, shutil
import batch_state as B

fails = []
def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        fails.append(name)


root = tempfile.mkdtemp(prefix="cal-bs-")
try:
    check("missing file returns 1", B.current_batch_id(root) == 1)
    check("advance returns 2 on first advance", B.advance_batch_id(root) == 2)
    check("file persists 2", B.current_batch_id(root) == 2)
    check("advance again returns 3", B.advance_batch_id(root) == 3)

    rubric_dir = os.path.join(root, "reference"); os.makedirs(rubric_dir)
    open(os.path.join(rubric_dir, "fit-rubric.md"), "w").write("RUBRIC_V3_FIXTURE")
    B.snapshot_rubric(root, 3)
    snap = os.path.join(root, "state", "batches", "3", "rubric-before.md")
    check("snapshot exists at expected path", os.path.exists(snap))
    check("snapshot matches source", open(snap).read() == "RUBRIC_V3_FIXTURE")

    open(os.path.join(root, "state", "batches", "current.txt"), "w").write("not-an-int\n")
    check("malformed file returns 1", B.current_batch_id(root) == 1)
finally:
    shutil.rmtree(root)

print()
print("FAILED:", fails if fails else "none")
raise SystemExit(1 if fails else 0)
