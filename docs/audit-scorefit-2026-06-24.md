# Audit & score-fit design — 2026-06-24

Workshop note (no verb reads this). Adversarial whole-codebase assessment + external
career-ops research + score-fit v0 design. Source: workflow wf_8577e29b (67 agents, 35
confirmed findings, each independently verified; 5 research angles). Disposition recorded
against each: FIXED this scope · DEFERRED · CLEAN.

## Part 1 — Assessment (devil's advocate)

### Blockers — score-fit could not be built well without these (all FIXED this scope)
- **mod-1 — the rubric was PROSE, not DATA.** D024 mandates a variable *table* the engine
  iterates; fit-rubric.md buried weights in headings. FIXED: fit-rubric.md v3 is now a
  machine table (`id|variable|kind|weight|floor|how-to-read`), 21 rows, validated.
- **mod-2 — weights didn't normalize** (summed to 94, no denominator; spine floor-gate had
  no number). FIXED: exact integer weights summing to 100, numeric spine floors (0.4), and
  the engine normalises by assessed-weight so a weight edit never rebases prior scores.
- **score.md schema violated D018/D019** (one blended `score`+`verdict`; odds model lived
  only in decisions.md). FIXED: architecture.md schema is now fit + odds + band +
  rubric-version + screen; `reference/odds-rubric.md` created in score-fit's read path.
- **cal-1 — `verdict` field collision** (machine writing `verdict` violates CLAUDE.md "never
  invent a verdict" and overwrites the human training label). FIXED: machine field renamed
  `screen:` (reject/flag/pass); `verdict:` left empty for the human, gut-first.
- **cal-2 — rubric-version stamp absent.** FIXED: stamped on every score.md (D025).

### Funnel / data integrity
- **jd-1 — the one jd.md was corrupted** (two roles spliced). FIXED: removed the stray
  "Head of Accounting Operations" sentence from the graphcore jd.md.
- **comp-1 — scout comp gate £50k vs the £60k floor.** FIXED: scout.py hard floor → £60k,
  the "£80k soft floor" string reworded to the D026 graduated-curve framing.
- **subject-1 / jd-2 — graphcore is out-of-family, would auto-reject.** USED as the
  intended negative control; a real in-family PASS (Accenture) was ingested for contrast.
- **wd-1 (multi-location London drop), wd-2 (silent malformed-registry drop), wd-3
  (searchText body-match), wd-5/wd-8 (throttle / test gaps)** — DEFERRED to a discovery
  hardening pass; real but not score-fit blockers.
- **targets-prestige-1 — targets.md stale** (prestige as near-gate vs L004 multiplier).
  FIXED: targets.md prestige section rewritten to multiplier + band-router.

### Cleanups & clean bills
- **render.py** dead/orphaned + hardcoded `~/Downloads` paths + stale coverage note.
  FIXED: deleted.
- **mod-1 naming** (scout→discovery drift in architecture.md + ingest). FIXED.
- CLEAN: PII/secrets correct (resume PDF + register gitignored); D029 authoring baseline
  conformant (no docs/ reads, no MUST/NEVER tables).

## Part 2 — Improvements adopted (research-backed)

Scanned santifer/career-ops (the donor), ResumeLM, OpenResume, Resume-Matcher,
proficiently-claude-skills, and the LLM-judge / calibration literature. Adopted as
MECHANISMS while keeping the bespoke rubric:
- **Decomposed, evidence-gated scoring** — one LLM judgment per rubric variable, then a
  deterministic Python weighted sum (DeCE: r=0.78 decomposed vs 0.35 holistic). Each verdict
  carries a verbatim quote the engine string-matches back into jd.md (Rulers evidence gate);
  `CANNOT_ASSESS` is the abstention primitive. This is the score-fit core.
- **Fixed-dumb engine over a data table** (Fowler "limited rules engine"; DMN
  `decide()→{result, rows_fired, why}` as the score.md audit-trail shape; WSM normalized
  weights; versioned rubric for comparability).
- **career-ops report scaffold** — its per-requirement→evidence "Block B" mapping is the
  shape of score.md's traceable body. Borrowed the skeleton, kept the rubric.
- **Calibration deferred** (events-per-variable: ~0 weights fittable at N=5, 2-4 at N=50).
  Weights stay v1 hypotheses; later, Bradley-Terry/logistic on pairwise verdicts regularized
  to the hand-set prior. Confirms D025 Phase-1.
- **Embeddings rejected as the scorer** — cosine fails on negated qualitative criteria
  ("strategy NOT codebase"), correlates ~0 with judge quality, breaks stdlib-only. Left as a
  disabled, v1 data-flag idea only.

## Part 3 — Deferred follow-ups (not blockers)
- Discovery hardening: wd-1 (multi-location London drop — make it a logged, not silent,
  miss), wd-2 (fail-loud on malformed registry rows), wd-3 (title gate on Workday rows),
  wd-5 (throttle/jitter), wd-8 (network-failure + malformed-registry + Madrid-primary tests).
- Calibration loop wiring (cal-3 per-row version pin on the GAP; cal-6 the D022 immutable
  audit-trail file does not exist yet).
- score.md `odds` is v0-provisional until the `competition` factor is grounded from real roles.
- ingest: the visa-refusal-in-body marker (Q6) still open.
