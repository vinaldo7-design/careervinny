# CareerVinny — STATUS (build stack)

Topmost `next` is the current scope. A scope is done when it PROVES its claim.

## next — score-fit v0: jd.md + rubric → score.md
Score a stored jd.md against fit-rubric.md into a score.md — fit (gated weighted sum) and
odds (product), banded, with a `rubric-version:` stamp (D018 · D019 · D023 · D025). Reuse the
embedding mechanics; keep the bespoke rubric — that is the moat. The funnel now has live
input end to end: discovery surfaces gate-passing Workday roles → ingest converts a survivor
→ score-fit scores it.
Claim (the test): a real ingested role (graphcore-business-analyst-lead, or a fresh
Accenture/GSK Workday survivor once ingested) gets a fit score, an odds score, and a band,
each traceable to specific rubric rows, under a stamped rubric version.

## later
- **tailor-cv v0** — master-profile.md + jd.md → tailored CV draft (ResumeLM-style;
  lift career-ops's Playwright HTML→PDF + ATS template).
- **network v0** — draft outreach into the role folder (bespoke; human reviews + sends;
  adapt career-ops contacto/deep/cover material).
- **dashboard** — render from score.md.

## done
- **discovery v0** (2026-06-24) — PROVED. The Workday/Taleo blind spot is closed, FREE.
  Relocated the scout into the repo (`skills/discovery/`) and added a Workday `cxs` layer: a
  probe-verified, calibration-grown tenant registry (`reference/workday-registry.md`) + a POST
  poller reusing scout's eligibility gates and signals. One `--workday-only` run surfaced 144
  currently-live, gate-passing UK roles Greenhouse/Lever/Ashby cannot see — across ALL three
  target families (consulting 5, bank 92, pharma 47). Bullseye role-family #1, gate-passing,
  e.g. Accenture "Data & AI Strategy Manager" (London), GSK "AI/ML Engineer, Responsible AI"
  (London), AstraZeneca "Strategy Director — Clinical Development" (Cambridge). Q8 SETTLED
  (cxs-only; JobSpy + Playwright deferred — neither reaches Workday). 18 fixture tests pass.
  Proof: `skills/discovery/proof-discovery-v0.md`. (decisions D014 · D027 · Q8 · audit 2026-06-23)
- **ingest v0** (2026-06-23) — PROVED. SKILL.md authored to Anthropic's Agent Skills
  standard (D029): description-carried triggers, a lean imperative body that explains the
  WHY (no rigid MUST/NEVER tables);
  one real gate-passing role ingested end-to-end →
  `state/roles/graphcore-business-analyst-lead/jd.md` (full clean body, complete
  frontmatter, fetched once via the Greenhouse JSON API). En route, strategic roles that
  refuse sponsorship in-body were correctly screened out — see Q6.
