#!/usr/bin/env python3
import os, shutil, tempfile, time
import scout_runner as SR

fails = []
def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        fails.append(name)


root = tempfile.mkdtemp(prefix="sr-")
try:
    s0 = SR.status(None, root)
    check("status before any job: state == none", s0["state"] == "none")

    fake_dir = os.path.join(root, "skills", "discovery", "scripts"); os.makedirs(fake_dir)
    fake = os.path.join(fake_dir, "scout.py")
    open(fake, "w").write("#!/usr/bin/env python3\nimport sys, time\nprint('domains=' + ','.join(sys.argv[1:]))\ntime.sleep(0.3)\nprint('done')\n")
    os.chmod(fake, 0o755)

    started = SR.start(["consulting", "ai-lab"], root)
    check("start returns job_id", bool(started.get("job_id")))
    check("start returns pid > 0", started.get("pid", 0) > 0)

    try:
        SR.start(["bank"], root)
        check("two jobs raises", False)
    except RuntimeError:
        check("two jobs raises RuntimeError", True)

    for _ in range(50):
        s = SR.status(None, root)
        if s["state"] in ("done", "failed"):
            break
        time.sleep(0.05)
    s = SR.status(None, root)
    check("status after completion: state == done", s["state"] == "done")
    check("returncode == 0", s.get("returncode") == 0)
    check("log_tail contains 'done'", "done" in (s.get("log_tail") or ""))
finally:
    shutil.rmtree(root)

print()
print("FAILED:", fails if fails else "none")
raise SystemExit(1 if fails else 0)
