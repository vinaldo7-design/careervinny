# CareerVinny — STATUS (build stack)

Topmost `next` is the current scope. A scope is done when it PROVES its claim.

## next — tailor-cv v0: master-profile.md + jd.md → tailored CV draft
Render a tailored CV from the decomposed master-profile blocks against a scored role's jd.md
(ResumeLM-style; lift career-ops's Playwright HTML→PDF + ATS template). Human reviews + never
auto-sends. Natural successor: the funnel now produces scored, banded roles (score.md), so
tailoring has a ranked target to aim at.
Claim (the test): a gate-passing scored role (e.g. accenture-data-ai-strategy-manager) yields
a tailored CV draft that leads with the role-relevant master-profile blocks, written into the
role folder.

## later
- **network v0** — draft outreach into the role folder (bespoke; human reviews + sends;
  adapt career-ops contacto/deep/cover material).
- **dashboard** — render from score.md.

## done
- **score-fit v0** (2026-06-24) — PROVED, end-to-end. fit-rubric.md refactored from prose to a
  machine-iterable variable table (D024 implemented: 21 rows, weights sum 100, numeric spine
  floors); new reference/odds-rubric.md (second axis). A stdlib engine (skills/score-fit/scripts/
  scorer.py) takes one evidence-gated judgment per variable and deterministically computes fit
  (normalised weighted sum + spine floor-gate + comp curve + ESG×AI) and odds (anti-compensatory
  product) → score.md with a band, a MACHINE screen (never the human verdict), a rubric-version
  stamp, and a row-by-row traceable body. 34 engine fixture tests pass. Funnel proven end-to-end:
  discovery (Accenture survivor) → ingest (NEW Workday cxs detail path) → score-fit. Discriminates
  the easy poles (bullseye vs out-of-family negative control; the hard cases — IC-tell, prestigious-
  but-frontier-free, comp-stated — await real verdicts): Accenture "Data & AI Strategy Manager" →
  fit 92 / odds 0.24 / band moonshot (provisional) / screen flag (recency); graphcore "Lead Business
  Analyst" (frontier-free negative control) → screen reject on the spine floor, fit 13. Audit fixes folded in (comp £60k, render.py deleted,
  targets prestige, score.md schema, scout→discovery naming). Audit: docs/audit-scorefit-2026-06-24.md.
  (decisions D018 · D019 · D023 · D024 · D025 · D030 · audit wf_8577e29b)
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
