#!/usr/bin/env python3
import json, os, tempfile, shutil
import queue as Q

fails = []
def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        fails.append(name)


def make_role(root, key, screen, fit, band, posted="2 days"):
    d = os.path.join(root, "state", "roles", key)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "jd.md"), "w", encoding="utf-8").write(
        "---\ncompany: %s\ntitle: %s\nlocation: London\nposting-age: %s\n---\n\nbody <script>x</script>\n"
        % (key.split("-")[0].title(), key, posted))
    open(os.path.join(d, "extraction.json"), "w").write("{}")
    open(os.path.join(d, "score.md"), "w", encoding="utf-8").write(
        "---\nscreen: %s\nfit: %s\nband: %s\nrubric-version: 3\n---\nbody"
        % (screen, fit, band))


root = tempfile.mkdtemp(prefix="cal-q-")
open(os.path.join(root, "calibration-log.jsonl"), "w").close()
make_role(root, "alpha-strategy-manager", "pass", 88, "safety")
make_role(root, "beta-business-analyst", "reject", 13, "null")
make_role(root, "gamma-ai-engineer", "flag", 72, "achievable")
make_role(root, "delta-already-labelled", "flag", 70, "stretch")

# Mark delta as already labelled
open(os.path.join(root, "calibration-log.jsonl"), "w").write(
    '{"role_key":"delta-already-labelled","verdict":"pursue"}\n')

q = Q.build_queue(root)
keys = [r["key"] for r in q]
check("already-labelled role excluded", "delta-already-labelled" not in keys)
check("queue has 3 remaining roles", len(q) == 3)
check("pass-screen role comes first", keys[0] == "alpha-strategy-manager")
check("reject comes last", keys[-1] == "beta-business-analyst")
check("each row carries machine fields", all("fit" in r and "screen" in r for r in q))

payload = Q.load_role(root, "alpha-strategy-manager")
check("load_role returns jd_md", payload["jd_md"].startswith("---"))
check("load_role returns jd_html_safe — < escaped", "<script>" not in payload["jd_html_safe"])
check("load_role returns jd_html_safe — &lt; present", "&lt;script&gt;" in payload["jd_html_safe"])
check("load_role exposes extraction", isinstance(payload["extraction"], dict))
check("load_role exposes score frontmatter", payload["score_frontmatter"]["fit"] == "88")

shutil.rmtree(root)

# Cap test: with > BATCH_SIZE roles, queue is sliced to BATCH_SIZE.
root2 = tempfile.mkdtemp(prefix="cal-q-cap-")
open(os.path.join(root2, "calibration-log.jsonl"), "w").close()
for i in range(Q.BATCH_SIZE + 5):
    make_role(root2, "epsilon-%02d-strategy" % i, "pass", 80 - i, "safety")
q2 = Q.build_queue(root2)
check("queue capped at BATCH_SIZE", len(q2) == Q.BATCH_SIZE)
shutil.rmtree(root2)

print()
print("FAILED:", fails if fails else "none")
raise SystemExit(1 if fails else 0)
