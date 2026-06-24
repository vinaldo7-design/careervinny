#!/usr/bin/env python3
import json, os, tempfile, shutil
import queue as Q

fails = []
def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        fails.append(name)


def make_role_with_domain(root, key, screen, fit, band, domain="", posted="2 days"):
    d = os.path.join(root, "state", "roles", key)
    os.makedirs(d, exist_ok=True)
    domain_line = ("domain: %s\n" % domain) if domain else ""
    open(os.path.join(d, "jd.md"), "w", encoding="utf-8").write(
        "---\ncompany: %s\ntitle: %s\nlocation: London\nposting-age: %s\n%s---\n\nbody\n"
        % (key.split("-")[0].title(), key, posted, domain_line))
    open(os.path.join(d, "extraction.json"), "w").write("{}")
    open(os.path.join(d, "score.md"), "w", encoding="utf-8").write(
        "---\nscreen: %s\nfit: %s\nband: %s\nrubric-version: 3\n---\nbody"
        % (screen, fit, band))


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

# Cap test: with roles spread across enough distinct industries to reach BATCH_SIZE,
# total is still capped at BATCH_SIZE. Use 10 industries x (CAP_PER_INDUSTRY + 2) roles each
# so each industry would exceed its cap, but total available >= BATCH_SIZE.
root2 = tempfile.mkdtemp(prefix="cal-q-cap-")
open(os.path.join(root2, "calibration-log.jsonl"), "w").close()
industries = ["tech", "finance", "pharma", "retail", "energy",
              "media", "transport", "health", "legal", "education"]
idx = 0
for ind in industries:
    for j in range(Q.CAP_PER_INDUSTRY + 2):
        make_role_with_domain(root2, "epsilon-%02d-%s" % (idx, ind), "pass", 80 - idx, "safety",
                              domain="%s:strategy:manager" % ind)
        idx += 1
q2 = Q.build_queue(root2)
check("queue capped at BATCH_SIZE", len(q2) == Q.BATCH_SIZE)
shutil.rmtree(root2)

# --- Industry diversity tests ---

# Test: 8 consulting + 2 pharma + 2 bank -> at most 4 consulting, all pharma+bank included
root3 = tempfile.mkdtemp(prefix="cal-q-div-")
open(os.path.join(root3, "calibration-log.jsonl"), "w").close()
for i in range(8):
    make_role_with_domain(root3, "cons-%02d" % i, "pass", 90 - i, "safety", domain="consulting:strategy:manager")
for i in range(2):
    make_role_with_domain(root3, "pharm-%02d" % i, "pass", 80 - i, "safety", domain="pharma:research:scientist")
for i in range(2):
    make_role_with_domain(root3, "bank-%02d" % i, "pass", 70 - i, "safety", domain="bank:operations:analyst")
q3 = Q.build_queue(root3)
consulting_count = sum(1 for r in q3 if r["industry"] == "consulting")
pharma_count = sum(1 for r in q3 if r["industry"] == "pharma")
bank_count = sum(1 for r in q3 if r["industry"] == "bank")
check("industry-diverse: consulting capped at CAP_PER_INDUSTRY", consulting_count <= Q.CAP_PER_INDUSTRY)
check("industry-diverse: all pharma included", pharma_count == 2)
check("industry-diverse: all bank included", bank_count == 2)
check("industry-diverse: total <= BATCH_SIZE", len(q3) <= Q.BATCH_SIZE)
shutil.rmtree(root3)

# Test: 30 consulting roles -> exactly CAP_PER_INDUSTRY (not BATCH_SIZE)
root4 = tempfile.mkdtemp(prefix="cal-q-only-cons-")
open(os.path.join(root4, "calibration-log.jsonl"), "w").close()
for i in range(30):
    make_role_with_domain(root4, "cons-%02d" % i, "pass", 90 - i, "safety", domain="consulting:strategy:manager")
q4 = Q.build_queue(root4)
check("single-industry: capped at CAP_PER_INDUSTRY not BATCH_SIZE", len(q4) == Q.CAP_PER_INDUSTRY)
shutil.rmtree(root4)

# Test: roles without domain frontmatter line get industry="unknown" and are still capped
root5 = tempfile.mkdtemp(prefix="cal-q-unknown-")
open(os.path.join(root5, "calibration-log.jsonl"), "w").close()
for i in range(10):
    make_role(root5, "nodomain-%02d" % i, "pass", 85 - i, "safety")
q5 = Q.build_queue(root5)
unknown_count = sum(1 for r in q5 if r["industry"] == "unknown")
check("no-domain roles bucketed as unknown", unknown_count > 0)
check("unknown industry capped at CAP_PER_INDUSTRY", unknown_count <= Q.CAP_PER_INDUSTRY)
shutil.rmtree(root5)

# Test: industry field is present on each returned row
root6 = tempfile.mkdtemp(prefix="cal-q-field-")
open(os.path.join(root6, "calibration-log.jsonl"), "w").close()
make_role_with_domain(root6, "fieldtest-01", "pass", 88, "safety", domain="tech:engineering:swe")
make_role(root6, "fieldtest-02", "pass", 75, "safety")
q6 = Q.build_queue(root6)
check("industry field present on all rows", all("industry" in r for r in q6))
shutil.rmtree(root6)

# Test: load_role includes industry field
root7 = tempfile.mkdtemp(prefix="cal-q-loadrole-")
open(os.path.join(root7, "calibration-log.jsonl"), "w").close()
make_role_with_domain(root7, "lr-test-01", "pass", 88, "safety", domain="fintech:product:manager")
payload_lr = Q.load_role(root7, "lr-test-01")
check("load_role returns industry field", "industry" in payload_lr)
check("load_role industry parsed correctly", payload_lr["industry"] == "fintech")
shutil.rmtree(root7)

print()
print("FAILED:", fails if fails else "none")
raise SystemExit(1 if fails else 0)
