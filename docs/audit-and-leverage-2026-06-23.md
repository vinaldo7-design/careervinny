# Audit & leverage research — 2026-06-23

Workshop note (no verb reads this). Audit of the repo vs the objective, plus field
research on what to leverage. Research run: wf_b29facf3-000 (102 agents, 23/25 claims
confirmed).

## Part 1 — Audit: what's there, is it right / needed

**Verdict:** logic strong and nearly done; build barely started; discovery blind on the #1 role family.

- **Logic spine (`reference/`) — strong, keep.** north-star → targets → fit-rubric → lessons coheres; the revealed-preference calibration loop (L001–L009) is the real asset and the right way to "score by my logic." fit-rubric v2 is well-built.
- **⚠️ `targets.md` stale** — still lists "£100k+ base — HARD GATE" (line 17); contradicts D026 + fit-rubric v2 (£60k floor + penalty curve). Fix with the rubric update.
- **Discovery — biggest gap.** Only `cc-batch-scout-spec.md` + one run. Blind on consulting/banks/pharma (Workday/Taleo, no public API) = role-family #1.
- **`score-fit` — not built** (logic exists, skill doesn't).
- **`tailor-cv` / `network` — entirely unbuilt** (half the objective).
- **Human-in-loop — sound** (withheld tools enforce it).
- **Proportionality** — heavy meta-structure, almost no working code. Next move: thinnest working slice + leverage, not more spec.

## Part 2 — Leverage map (don't reinvent the wheel)

| Stage | Off-the-shelf? | Adopt | Notes |
|---|---|---|---|
| Discovery — boards | ✅ strong | **JobSpy** (LinkedIn/Indeed/Glassdoor/Google/ZipRecruiter) | ZERO ATS coverage, ~1000-job cap, LinkedIn rate-limits → needs proxies. Pair with an ATS layer. |
| Discovery — ATS depth | ✅ build-pattern or buy | **jobhive / Feashliaa pattern** (build) or **Fantastic.jobs / TheirStack** (buy) | The blind-spot fix — see Part 3. |
| Fit-scoring | ✅ solved pattern | LLM-structure + **HF embeddings** (nomic-embed-text-v1.5, Apache-2.0) + cosine | Reuse the *mechanics*; KEEP the bespoke rubric/calibration — that's the differentiator. |
| CV tailoring / ATS score | ✅ | **ResumeLM** (base+tailored, ATS score, keyword opt, cover-letter) | Bolt-on; has no discovery. |
| Outreach drafting (human-in-loop) | ❌ none found | — | **Genuinely bespoke.** Build native on the LLM layer. |
| Auto-apply | ⛔ avoid | ~~AIHawk~~ | LinkedIn-only Selenium, brittle, archived ~May 2026, and *auto-applies* (breaks human-in-loop). Cautionary, not a target. |

## Part 3 — Scout mechanism: reaching Workday/Taleo (the fix)

**Key insight: the Workday API is the easy part; knowing which employers exist is the hard part.**
- Workday exposes an undocumented **public `cxs` JSON endpoint** — `https://{co}.wd{n}.myworkdayjobs.com/wday/cxs/{co}/{site}/jobs` — works **without login** for most tenants.
- Everyone solves discovery with a **curated tenant registry** (`company|wd#|site_id`): ApplyPilot (48 Workday portals), Feashliaa/job-board-aggregator (`workday_companies.json` + `fetch_company_jobs_workday`), jobhive/ats-scrapers (`workday.py`/`taleo.py`/`successfactors.py`; Workday alone ≈ 449k jobs, > Greenhouse+Lever combined).
- **Anti-bot:** tiered parse cascade (JSON-LD → CSS → AI extraction) for arbitrary career sites; stealth headless browser (Browserbase) ONLY for the few behind Akamai (Meta, Tesla). Workday `cxs` blocks pagination under load.

**Three paths:**
1. **BUILD** — add an ATS-direct layer: curated Workday/Taleo registry for your named targets (Accenture, BCG, McKinsey, Deloitte, JPM, Goldman, GSK, AstraZeneca…) + poll `cxs`. Contained, proven, MIT-licensed patterns to copy (jobhive, Feashliaa).
2. **BUY** — Fantastic.jobs (54 ATS, 875k Workday jobs, 4.7k cos; PwC/Accenture/Citi named) or TheirStack (346k sources incl. Workday/Taleo/SuccessFactors). ⚠️ vendor-reported/unaudited; **pharma NOT confirmed in any source**; spot-check your employers first.
3. **SUPPLEMENT** — SerpApi/JSearch (Google-for-Jobs): only reach what employers expose to Google's crawl. Breadth supplement, not reliable enterprise depth.

## Caveats
- Commercial coverage figures are vendor-reported, unaudited. **Pharma unproven** (your highest-value-but-weakest-evidenced family) — verify empirically before relying on a vendor.
- AGPL-3.0 (ApplyPilot) is copyleft — don't vendor its code into a closed pipeline. jobhive MIT, Feashliaa MIT code / CC-BY-NC data, JobSpy OK.

## Open questions (candidates for decisions.md)
1. **Build vs buy** the ATS layer (self-maintained registry vs Fantastic.jobs/TheirStack) — decide after a pharma spot-check + pricing.
2. Best-maintained crowd-sourced Workday tenant registries; auto-discovery (brute-force `wd{1-5}` subdomains, mine Google-indexed `myworkdayjobs.com` URLs, LinkedIn company→ATS map).
3. **Sequencing — does this reopen D-Q1 (ingest-first)?** Audit says discovery coverage is the #1 gap; Q1 settled ingest-first. Which is the top STATUS scope?

## Sources
GitHub: Pickle-Pixel/ApplyPilot · kalil0321/ats-scrapers (jobhive) · Feashliaa/job-board-aggregator · speedyapply/JobSpy · olyaiy/resume-lm · feder-cr/Jobs_Applier_AI_Agent_AIHawk. Commercial: fantastic.jobs/api · theirstack.com · serpapi.com · openwebninja.com (JSearch). Paper: MDPI Electronics 14(24):4960.
