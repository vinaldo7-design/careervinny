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
- **calibrate dashboard v0** (2026-06-24) — local clickable dashboard at
  `skills/calibrate/scripts/server.py` (stdlib HTTP, no deps). Walks the queue of scored roles
  one at a time; shows JD link + collapsible JD + gates (HIT/MISS pills) + variable verdicts
  (MET/PARTIAL/UNMET color-coded) BEFORE the score. The /score route is server-locked (HTTP 423)
  until a /verdict POST lands — anti-anchoring is enforced mechanically, not by convention.
  Verdict + one-line reason append to calibration-ledger.md (with `key:` + `rubric:` tokens) AND
  calibration-log.jsonl (with the extraction snapshot). `review.py` summarises divergences per
  variable after each ≥20-verdict batch and writes `status: proposed` deltas to lessons.md —
  never editing the rubric, never adding or removing a gate autonomously. Queue is capped at
  BATCH_SIZE=20. `check.sh` now also runs the calibrate pure-fn tests; the ledger regression
  guard goes red on any contradiction > 1 band. Anti-anchoring hardened: path traversal
  containment, score-field-stripping in queue JSON, Content-Length cap, JSON-encoded template
  substitution, lock-guarded _VERDICT_INDEX read.
  (D031 · adversarial-review build wave: tasks 1-9)
- Batch loop (2026-06-24) — `/batch/propose` returns proposal cards (weight + gate) with reasoning, sample roles, magnitude, and downstream re-band; `/batch/apply` applies only Accepted weight changes atomically, reverts on red, writes `state/batches/<N>/calibration.md`. Defer queue carries undecided proposals into the next batch. UI: "Load batch" preview shows industry mix; "Scout fresh" runs the discovery scout in the background with a polling chip; "Done — review proposals" opens the ratify modal. (D034 v2, D035, D036, D037, D038)
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
