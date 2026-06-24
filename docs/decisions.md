---
name: decisions
description: Architectural decision log for CareerVinny. Organized by EXECUTION URGENCY, not chronology — LIVE (constrains current build), SETTLED-ACTIVE (decided, occasionally referenced), BEDROCK (hardened into architecture, fossil provenance). Read LIVE before building; read lower tiers only to reopen a settled question. D-numbers are stable addresses — an entry keeps its number when it moves tier. Append-only; supersede with a new dated entry rather than editing old ones.
status: v7, 2026-06-24 (D038 — deferred proposals re-surface until decided)
---

# CareerVinny — Decisions Log

Three tiers by execution urgency. LIVE = building against this now. SETTLED-ACTIVE
= decided, still referenced, not currently building against. BEDROCK = absorbed
into architecture.md, here for provenance only — one line each, full text
retrievable from version history if ever challenged. Entries promote/demote between
tiers as their urgency changes; D-numbers never change.

---

# ═══ LIVE (constrains the current / next build cycle) ═══

## D029 — Skill-authoring standard is Anthropic's Agent Skills guide, not addyosmani
SETTLED 2026-06-24 (Vinay). CareerVinny's own skills are authored to Anthropic's official
Agent Skills best practices (operationalised by the `skill-creator` skill): the description
field carries all when-to-use and is written slightly "pushy" against under-triggering; the
body is lean and imperative and explains the WHY rather than leaning on rigid MUST/NEVER
tables or excuse/red-flag checklists; progressive disclosure keeps SKILL.md < 500 lines with
optional scripts/ + references/. Supersedes the brief addyosmani/agent-skills-style structure
(Overview/When/Process/Rationalizations/Red-flags/Verification) used on ingest. Distinct from
the other two reference repos: obra/Superpowers = build METHODOLOGY (how we work);
santifer/career-ops = FEATURE donor (what we build). ingest/SKILL.md re-authored 2026-06-24.

## D030 — score-fit is a decomposed, evidence-gated scorer over a data-driven rubric
SETTLED 2026-06-24, calibrated by the wf_8577e29b audit + research. score-fit v0 architecture:
- **Rubric is DATA (D024 implemented).** fit-rubric.md v3 carries a machine-iterable variable
  table (id|variable|kind|weight|floor|how-to-read); the engine hardcodes no variable and iterates
  rows. Add a variable = add a row; change a weight = edit a cell. Weights are exact integers
  summing to 100, normalised by assessed-weight so an edit never rebases prior scores; spine traits
  carry a numeric floor (0.4). A new KIND of math is the only thing that touches engine code.
- **Decomposed + evidence-gated extraction.** One LLM judgment per variable {MET/PARTIAL/UNMET/
  CANNOT_ASSESS, verbatim quote, confidence}; a stdlib engine string-matches the quote back into
  jd.md (downgrades unverifiable) and combines deterministically. CANNOT_ASSESS = abstention
  (non-spine excluded from num+denom; spine = floor breach, never silently dropped). Beats a
  holistic 0-100 (DeCE r=0.78 vs 0.35). Embeddings REJECTED as the scorer (cosine fails on negated
  qualitative criteria; breaks stdlib-only) — left as a disabled v1 idea only.
- **score.md = two axes + screen, NOT verdict.** fit (0-100) and odds (0-1 product) stay separate
  (D018), banded (D019), rubric-version stamped (D025). Machine field is `screen:` (reject/flag/
  pass); `verdict:` (pursue/on-ramp/no) is the HUMAN field, left empty — score-fit never writes it
  and score.md is not surfaced before the gut verdict (CLAUDE.md anti-anchoring).
- **Calibration is OUT of v0** (events-per-variable: ~0 weights fittable at N=5). Weights stay v1
  hypotheses; later, data nudges a few high-signal weights regularised toward the prior (D025 Ph-2).
- **Prestige is a band-router, not a fit multiplier** (resolves the undefined-magnitude hole; L004).
- **Recency is a staleness guard, not an odds factor (2026-06-24, revised).** A posting older than
  `STALE_DAYS` (42, a tunable constant in scorer.py) is treated as likely-closed: held out of
  banding (band null) + flagged `likely-closed:verify-live` for live re-confirmation; it does NOT
  touch odds. Fresh/at-threshold postings score normally. Rationale (Vinay): an old ATS req is a
  still-open question, not a smooth attainability gradient — hold it for verification rather than
  silently decaying odds. (Supersedes the brief odds-factor implementation.)
- **Competition dropped from odds (2026-06-24).** odds = seniority_match × requirement_match.
  How-contested can't be measured without market data; a 0.5 placeholder just halved every odds
  for no signal, so it is removed (refines D023's three-factor odds; odds-rubric → v2). The two
  remaining factors are read from the JD vs master-profile.
Files: skills/score-fit/{SKILL.md, scripts/scorer.py, scripts/test_scorer.py}; reference/
{fit-rubric.md v3, odds-rubric.md}. Proven end-to-end on graphcore (reject, spine floor) + Accenture
(fit 92, moonshot) — the latter via a NEW ingest Workday-cxs-detail path.

## D031 — Anti-anchoring is enforced by the server, not by convention
SETTLED 2026-06-24. The calibrate dashboard's /score endpoint returns HTTP 423 until a /verdict
POST for the same role lands in calibration-log.jsonl. The browser cannot retrieve the machine
fit/odds/band/screen until Vinay has clicked his gut verdict + typed a one-line reason. This
moves the "never anchor the human" rule (CLAUDE.md) from a prose discipline to a mechanical
property of the server. Verdict log rows additionally snapshot the live `rubric-version` so a
later re-fit knows which ruler labelled which role (D025).
- Gates: the dashboard NEVER edits fit-rubric.md and NEVER autonomously adds or removes a gate
  row, even with in-flight verdict approval. The strongest action review.py takes is appending
  a `status: proposed` delta to lessons.md, naming the variable and the role.
- Append-only: every verdict appends; never rewrites a past row (CLAUDE.md).
- One rubric per batch: if rubric-version changes mid-batch the POST returns 409 unless the
  user explicitly acknowledges in the browser.
- Anti-anchoring hardened (adversarial-review build wave): path traversal containment,
  score-field-stripping in queue JSON, Content-Length cap, JSON-encoded template substitution,
  lock-guarded _VERDICT_INDEX read. These are load-bearing mechanical guarantees, not conventions.
- Queue capped at BATCH_SIZE=20; `review.py` summarises after each ≥20-verdict batch.
Files: skills/calibrate/{SKILL.md, scripts/server.py, scripts/review.py, scripts/log.py,
scripts/queue.py}.

## D032 — Calibration batches are diversity-sampled by industry
SETTLED 2026-06-24. The queue builder takes the top sort-ranked roles but caps each industry at CAP_PER_INDUSTRY = 4 of BATCH_SIZE = 20. This forces each batch to span at least 5 industries (or as many as the role pool offers), so calibration spreads across the market instead of pooling on one vertical. Industry is sourced from jd.md frontmatter `domain: <industry>:<archetype>` which is seeded from reference/domain-map.md.
- The "unknown" industry is a normal bucket (same cap). Untagged roles do not vanish, but they also do not crowd out tagged diversity.
- Diversity is enforced on industry only; archetype is currently informational. Future: layer archetype-aware sampling once enough industries are populated.
- Effect on calibration: review.py batch_summary computes per-industry hit rates (% pursue / mean fit) so the user can see which industries fit best as labels accumulate.
Files: skills/calibrate/scripts/queue.py (CAP_PER_INDUSTRY), reference/domain-map.md, state/roles/<key>/jd.md (domain frontmatter).

## D033 — Per-batch overview is server-rendered, not a separate report
SETTLED 2026-06-24. The /batch-summary route + dashboard panel give the user verdict-mix, per-industry hit rates, fit distributions by verdict bucket, divergences, and proposed deltas as a single click after a batch. This replaces "run review.py separately to see the picture" with "see the picture in the same UI that captured the verdicts". review.py --batch-summary CLI remains for headless / scriptable use.
Files: skills/calibrate/scripts/{server.py, review.py, static/app.js, templates/index.html}. Default window is BATCH_SIZE=20 (last 20 verdicts, matching the CLI); `?window=all` returns lifetime aggregates.

## D034 v2 — Weight + gate proposals are propose-ratify, not auto-apply
SETTLED 2026-06-24. On batch close, `/batch/propose` returns a list of proposal cards (weight nudges + gate add/remove) with reasoning, sample roles, magnitude, and downstream re-band. Nothing edits `reference/fit-rubric.md` until the user clicks Accept on cards in the dashboard and `/batch/apply` is called with the accepted ids. Apply is atomic (one rubric edit per batch); on `check.sh` red the rubric reverts byte-for-byte and the batch counter does NOT advance. Gate accepts are recorded in the audit but the rubric is not auto-edited — gate add/remove is a structural change the user makes by hand.
Files: skills/calibrate/scripts/proposals.py, apply_proposals.py, server.py (_handle_batch_propose, _handle_batch_apply).

## D035 — Per-batch audit at state/batches/<N>/calibration.md
SETTLED 2026-06-24. Every `/batch/apply` writes a markdown audit recording verdict mix, accepted weight changes (old → new), accepted gate decisions (rubric not auto-edited), rejected proposals, deferred proposals, guard status, and contradicting roles on revert. The file is the durable record — diffable, re-runnable, and the only place outside `calibration-log.jsonl` that links a batch to its rubric change.

## D036 — Gate proposals carry low-confidence flag
SETTLED 2026-06-24. Gate-add (perfect-predictor heuristic, requires N >= 6 samples) and gate-remove (not-fired-in-3-batches heuristic) proposals are tagged `confidence: "low"` in the proposal card. UI renders them with a "low confidence" pill and a yellow border. They never auto-apply (see D034 v2). The reasoning text on each gate card explicitly says "consider" rather than asserting. The discovery scout's `--domains` flag is live (domains_to_verticals maps industries to registry verticals) — scout filtering is functional, not a placeholder.

## D037 — Reasoning is computed, not narrated
SETTLED 2026-06-24. Each proposal card's `reasoning` field is built from verdict counts + rubric weights + variable names — no LLM call at close time. Format: "You said X on N roles where the extraction marked Y as Z. The rubric currently weights Y at W. The pattern suggests …". This keeps batch close deterministic, fast, and offline. If richer narrative is wanted in future, it can be added at audit-render time (a separate concern).

## D038 — Deferred proposals re-surface until decided
SETTLED 2026-06-24. The defer queue is an append-only event log at `state/batches/proposal-events.jsonl` recording `{proposal_id, status, batch_id, payload?}`. A proposal's current state = latest event for its id. Deferred proposals appear in the next batch's `/batch/propose` response under a `deferred` list (annotated with `deferred_from_batch: <id>`). Accept or Reject drops them from the queue; deferring again is a safe no-op.

## D028 — Cowork dropped; Claude Code is the sole runtime
SETTLED 2026-06-22. Cowork was removed from the system entirely. Claude Code is now the
only surface that reads this repo and runs the skills — runtime, reader, and operator
infra collapse into it. Supersedes D012's tool division (Cowork = runtime). The ingest
auth-walled fallback (D014) is now a browser tool inside Claude Code, not Chrome-in-
Cowork. Historical Cowork references are retained as dated record (D012, DL001, DL003),
not live architecture.

## D014 — Ingestion is a narrowing funnel; discovery ≠ ingestion ≠ scoring
THE BIG ONE for scale. Driving Chrome to read full rendered pages is token-brutal
at scale. Separate the three jobs:
- **scout (discovery):** CHEAP candidate list (title, company, URL, snippet) from
  job-board APIs/RSS. Wide net, minimal tokens. Does NOT read pages.
- **hard-gate pre-filter:** kill most candidates on metadata alone (visa, £60k floor,
  London, strategic-not-IC) BEFORE any expensive read.
- **ingest (conversion):** deep clean-read only on survivors. Prefer raw-HTML-
  strip over browser render; a browser tool in Claude Code is the auth-walled fallback only.
- **score-fit:** scores the clean jd.md files.
Token cost concentrates on the few roles that survive the cheap gates.

## D018 — Targets are one entity type scored on two axes that never collapse
A target is EITHER a role OR a person; both score on two independent axes: **fit**
(do I want this) and **attainability** (can I get this). NEVER averaged into one
number. Rejected: a single blended "lead score". Reason: a high-fit / low-
attainability target is a moonshot worth networking, not a bad lead to discard.
Fit is slow-moving; attainability moves every time Vinay ships, publishes, or
warms a contact. Stored separately in score.md frontmatter.

## D019 — Attainability is discretised into bands; bands sort wanted targets by reachability, never by fit
Role bands: **safety** (high fit, high odds — apply now) · **achievable** (apply
with real tailoring) · **stretch** (apply AND warm a contact in parallel) ·
**moonshot** (high fit, low odds — network-first). NO low-fit band: low fit dies
at the gate. Bands only sort roles Vinay ALREADY WANTS by reachability. Moonshot
formalises "don't shut the aspirational door early" — routed to the network flow,
never dropped. Same machinery as the visa-uncertain tier. Networking-odds for
people use the SAME axis: tie-strength × profile-reachability × message-quality
(the last being the only fully controllable multiplicand).

## D020 — Networking is not a parallel flow; it is the lever that raises attainability
The networking flow's output (a warmed relationship) feeds back into the job
flow's scoring as raised attainability, RE-BANDING a target upward (moonshot →
stretch → achievable). Networking MANUFACTURES attainability. Rejected: job-search
and networking as side-by-side equals. The relationship is producer→consumer.
Implication: the job flow produces banded roles before the network flow has
targets — EXCEPT moonshots, which are network-first by definition (D021).

## D021 — People are folder-per-entity in state/people/, mirroring state/roles/
`state/people/{name-slug}-{company-slug}/` holding profile.md, odds.md,
outreach.md, follow-up.md — same discipline as a role folder. Rejected: a contacts
table; people as fields on a role. A person links to roles via frontmatter
`roles:`; a role links to contacts via `contacts:`. Cross-folder edges are the
point (cf. D010). CONFIRMED 2026-06-18: people-as-folders ratified; networking
flow built incrementally, not fully deferred.

## D022 — Lessons generalization is agent-run and autonomous (supersedes L001 autonomy clause)
The 50-batch generalization pass that compacts lessons-audit.md into lessons.md
runs AUTONOMOUSLY — the agent writes generalized rules to the meta file without
per-batch human ratification. This SUPERSEDES L001's "never edited autonomously,
ratified by me" clause, FOR THE COMPACTION LAYER ONLY. Provenance is preserved by
the immutable append-only audit trail (lessons-audit.md), which is the audit
mechanism that stands in place of pre-write ratification. Rationale: Vinay's
decision, final — the value is a self-maintaining lessons substrate; the immutable
trail makes autonomous compaction auditable after the fact. Raw-instance capture
into the audit trail still reflects real decisions; autonomy applies to the
generalization step, not to inventing instances.

## D023 — Scoring math: fit ADDS, odds MULTIPLIES, spine has a floor-gate
Two numbers, two different operations, deliberately.
- **Fit = gated weighted sum.** Hard gates first (boolean reject). Then a weighted
  sum of want-it variables, each scored 0–1, times its weight; minus penalties;
  times the ESG×AI bonus. A weak trait can be offset by a strong one — correct for
  "do I want it."
- **Anti-lopsidedness: a SECOND floor-gate on the spine.** Frontier AND ladder must
  each clear a minimum before the sum counts. Stops a role huge on one spine trait
  and near-zero on the other from climbing on imbalance. The one good idea from
  TOPSIS (punish lopsidedness) without its machinery — a threshold, not a distance
  calculation.
- **Odds = product, not sum.** `seniority_match × requirement_match × competition`
  for roles; `tie_strength × reachability × message_quality` for people.
  Multiplication is inherently anti-compensatory: any near-zero factor collapses
  the result — correct, because you cannot GET a role you're three rungs too junior
  for, however well you match everything else.
- All traits normalised to 0–1 before combining. Odds carries a date stamp; fit
  does not (D018 decay asymmetry).
Rejected: full MCDA methods (TOPSIS/AHP) as the engine. Reason: they solve
closed-set ranking (pick 1 of N head-to-head); CareerVinny scores roles one-at-a-
time into bands over an open changing set. AHP additionally suffers rank-reversal
when the set changes — disqualifying for a longitudinal pipeline. TOPSIS stays a
possible LATER tool for a "rank my 8 live options this week" prioritisation view,
never the scoring engine.

## D024 — Variables are modular editable data; the engine is fixed and dumb
The scoring engine never hardcodes which variables it scores. The variable list
lives as an EDITABLE TABLE in fit-rubric.md: one row per variable, each with
weight, floor (if spine), and how-to-read-it-from-a-JD. The engine iterates the
rows and computes.
- Add a variable = add a row. Disable one = set weight 0 (keeps the history of
  having tried it). Shift preference = change a weight.
- Preferences WILL change over a career (front-load frontier at 27; ladder may
  dominate at 32). The system absorbs this by editing data, never rewriting the
  engine.
- The current variable list is a v1 HYPOTHESIS, not truth — almost certainly partly
  wrong. Likely dead weight: travel, client-facing (too low to move a band). Likely
  MISSING: specific people you'd work under, team newness, responsible-AI framing.
  Only real roles reveal which.
- A variable earns its place only if changing it would change a decision.
Rejected: hardcoding variables into scoring logic. Reason: stated preferences
diverge from revealed ones (A001 is a recorded instance), so the variable set must
be cheap to revise.

## D025 — Variables are validated by calibration from real verdicts, not introspection
Weights and the variable list start as guesses, corrected by labelled examples:
score real roles, record a would-pursue / wouldn't verdict + one-line why on each
(stored in score.md), let disagreements between verdict and score drive edits to
the variable table (D024) via the lessons loop.
- Phase 1 (~first 10 roles): find the SIGNALS, not the weights — too few labels to
  tune; value is catching gross errors and surfacing missed reactions.
- Phase 2 (~10–30): adjust weights from patterns.
- Phase 3 (enough data): weights stabilise; remaining disagreements are the hard
  calls.
The verdict field in score.md IS the training signal — over time score.md files
become the labelled dataset that turns guessed weights into calibrated ones. This
is why the first iterations exist: build the labelled set, not use the system in
anger yet.
Implication: score.md must carry a `rubric-version:` stamp so roles scored under
old weights stay comparable against roles scored under new ones — else the
longitudinal pipeline silently mixes incomparable scores.

### Open / sequencing (resolve before or during the current build cycle)
- ~~Q1 (MVP fork)~~ SETTLED: ingest-first. Build minimal ingest against ONE hand-
  fed role (hardest/sparsest source — a LinkedIn-alert-shaped role) to prove
  conversion + storage, THEN scout to feed it at volume.
- ~~Q2 (scout sources)~~ SETTLED: Tier-1 = public ATS APIs (Greenhouse/Lever/
  Ashby — no auth, structured JSON; Anthropic London via Greenhouse verified).
  Tier-2 = JobSpy-via-Apify (deferred). Tier-3 = LinkedIn job-alert emails →
  Gmail ingest (re-verify Gmail parsing in Claude Code). Slug list WEIGHTED toward
  consultancy AI practices, NOT frontier labs — labs are mostly IC-chaff for
  Vinay's profile (see DL003). >> SUPERSEDED by D027 (2026-06-19): the build-
  branded arms (QuantumBlack/BCG X) are ALSO chaff; fertile = responsible-AI/
  governance across verticals + classic-strategy + lab-commercial-strategy. <<
- Q3: D016 provenance gate mechanism. (open)
- Q4: thin moonshot-networking slice (contact-find + outreach-draft) concurrent
  with the job-flow MVP, or one proof-cycle later? Case for concurrent: moonshots
  are network-first, relationships warm slowly, 18-month runway already running.
- ~~Q5 (visa status)~~ SETTLED 2026-06-19: HPI / Global Talent (unsponsored) route
  NOT available to Vinay. The UK Skilled Worker visa-sponsorship hard gate STAYS
  SHUT — it remains a boolean hard gate in fit-rubric.md / targets.md, unchanged.
  Consequence: no gate dissolves, no target-set widening, lab fertility does NOT
  double (frontier labs stay IC-chaff per DL003). This closes the highest-leverage
  open unknown with the conservative outcome — the existing gates were correctly
  calibrated and need no revision.
- Q-scoring (NEW, partially resolved): job-odds inputs defined as seniority_match
  × requirement_match × competition. The competition factor is least-grounded —
  refine from real roles during calibration.
- jd.md template is the BRIDGE artifact: sections determined by the scoring
  variables (D023/D024) AND must preserve raw signal for FUTURE variables (team-
  newness, named people, responsible-AI framing) so adding a variable later never
  requires re-fetching a posting. Keep the extra in stored jd.md, NOT in score-fit's
  per-run read path. Draft it first in the ingest build chat (see ingest-handoff.md).
  >> UPDATE 2026-06-23 (ingest build): jd.md v0 SHIPPED — frontmatter per architecture.md
  (source-url, company, title, location, date-ingested, posting-age) + the FULL cleaned
  body verbatim. "Preserve raw signal" is met by storing the complete body (every future
  variable is derivable from it). Open sub-Q: also cache scout's derived signals as
  frontmatter, or keep them recomputable? Deferred to score-fit. First artifact:
  state/roles/graphcore-business-analyst-lead/jd.md. <<
- Q6 (visa authority — NEW 2026-06-23): definitive sponsorship is often stated only in
  the posting BODY, which ingest is first to read; the scout's register hit is "plausible",
  not sufficient. Gap: a refusing role can clear the metadata gate, get fully ingested, and
  be stored unflagged. Open: should ingest reject / write a visa-refused marker when the
  body refuses sponsorship? (3 Graphcore roles hit this 2026-06-23.) Not reopening Q5
  (policy unchanged) — this is about WHERE the authoritative read lives.
- ~~Q7 (role-key when title embeds seniority)~~ RATIFIED 2026-06-24: level word → seniority,
  remainder → slug. Applied again cleanly — "Data & AI Strategy Manager" ⇒
  `accenture-data-ai-strategy-manager` (Manager=seniority, data-ai-strategy=slug).
- ~~Q8 (discovery v0 approach)~~ SETTLED 2026-06-24 (Vinay, at discovery start): BUILD, free-only.
  v0 ships (a) ONLY — a curated, calibration-grown Workday `cxs` registry + poller, reusing
  scout's existing gates (visa/location/comp) and signal extraction. (c) JobSpy and (b) career-ops
  Playwright are DEFERRED, not dropped: the 2026-06-23 audit shows JobSpy has zero ATS coverage
  (cannot see Workday tenants) and Playwright is only needed for Akamai-walled sites (Meta/Tesla),
  so neither reaches the consulting/bank/pharma blind spot the claim targets. (d) buy rejected
  (free-only). The discovery engine is relocated INTO the repo: scout is brought in from
  ~/Downloads/ssdhj/scout/ to skills/discovery/scripts/ (repo = sole source of truth + portfolio;
  ~/Downloads becomes the archived donor); the tenant registry lives in reference/workday-registry.md
  as a first-class calibration-grown spine artifact. Original options preserved: (a) Workday cxs +
  registry, (b) career-ops Playwright fallback, (c) JobSpy public boards, (d) buy Fantastic.jobs/TheirStack.
- Ingest fetch tier-order (2026-06-23): ATS roles → ATS JSON endpoint (full content) >
  raw-HTML-strip (other pages) > browser (auth-walled). Refines D014's "strip preferred"
  (which contrasted strip vs browser, not vs ATS-JSON).

---

## D026 — £100k hard gate demoted to a graduated comp penalty (£60k floor)
SETTLED 2026-06-19. The £100k+ boolean gate silently killed high-fit roles
(empirical: Lloyds "Responsible AI Framework Specialist" £82-91k, a near-perfect
ESG×AI content match, died on comp alone). Repriced:
- **£80k = the floor below which a role is not worth attention** (true boolean —
  below this, reject).
- **£80k → £100k+ = a GRADUATED penalty** that shrinks as comp rises (steep near
  £80k, ~zero by £100k+). A role posted at £85-95k surfaces WITH a dent so Vinay
  decides whether fit justifies the negotiation; it is no longer silently dropped.
Rationale: at Vinay's rung the posted base is an OPENING position, not the deal —
a £85-95k role with his CS+DS+Oxford-DipAI+ESG-assurance stack is negotiated from
strength. A hard £100k filter discarded his own negotiating leverage pre-emptively.
This is the gate-list catching up to D023 (fit = gated weighted SUM): comp belongs
in the weighted sum as a penalty that ranks, not in the kill list.
Hard kills that REMAIN boolean (unchanged): visa sponsorship (D025-Q5),
London/UK-anchored, strategic-not-IC. Only the comp gate moved.
UPDATE 2026-06-22: floor is £60k, not £80k. £60–80k roles are KEPT and scored with a
graduated comp penalty (fit-rubric.md v2) — higher comp shrinks the penalty; they are
never silently rejected. The "£80k = floor below which a role is not worth attention
(reject below)" framing above is corrected: £60k is the hard floor, £80k sits mid-curve.

## D027 — Source-family re-weight from the 2026-06-19 live fertility sample
SETTLED 2026-06-19. Supersedes the QuantumBlack/BCG-X-weighted slug list implied
by the old D025-Q2 + ingest-handoff. Sampled six families against the real gates
(see DL005). New weighting:
- **FERTILE (Tier-1, weight heavily):**
  1. **Responsible-AI / AI-governance roles across regulated verticals** — NEW TOP
     FAMILY. Banks (Lloyds CDAO, JPM CDAO/SAIGE), pharma/publishing (Elsevier/RELX),
     energy (E.ON). Highest conversion BECAUSE it is Vinay's ESG×AI edge under a
     different name. Self-selects non-IC (you can't code an ethics framework);
     exploding across verticals on EU-AI-Act pressure.
  2. **Traditional consulting AI-strategy & AI-ethics practices** — Accenture,
     Deloitte, AI-Ethics consulting practices. London-solid, right rung,
     agency-bearing ("board papers", "strategic visions", baseline-tech-not-coding).
  3. **Frontier-lab COMMERCIAL-strategy** — Anthropic et al., but searched as
     "GTM Strategy / Strategic PM / Strategy & Operations", NOT "AI Strategy".
- **LUMPY (sample firm-by-firm, never weight as a block):** in-house bank
  AI-strategy. JPM fertile (named CDAO/Transformation function); Goldman low-yield
  (AI buried in Engineering/Product). JPM ≠ Goldman.
- **LOW-YIELD (demote to exception-hunt):** branded AI-BUILD arms — QuantumBlack,
  BCG X, BCG Platinion. IC-chaff for Vinay's profile, confirmed twice (DL003, DL005).
- **KEYWORD CORRECTION (load-bearing for scout):** hunt FUNCTIONS and VERBS, not
  AI-buzzword org names. Query set: "Responsible AI", "AI Governance", "AI Ethics",
  "AI Strategy & Transformation", "GTM Strategy", "Value Strategy", "Strategic
  Product Management", "AI Transformation Lead" — NOT bare "AI Strategy" or
  AI-branded sub-unit names (those return IC-build roles).
- **SENIORITY TOKEN MAP (load-bearing for the drift-guard):** VP@bank ≈
  Manager@consultancy ≈ Lead/Strategist@lab ≈ Senior-Associate@MBB ≈ Vinay's entry
  rung. Gate seniority on years+comp+reports, never the title string (DL005).
Status: settled as the map; the variable WEIGHTS within fit-rubric remain v1
hypotheses to be calibrated against real verdicts (D025), starting with Vinay's
20 live LinkedIn roles.

# ═══ SETTLED-ACTIVE (decided; referenced, not currently built against) ═══

## D008 — Knowledge moat lives in the existing KBAI vault, not a new store
Tier 3 = Vinay's existing Mini Vinny / KBAI Obsidian vault (typed graph + PPR),
not a new database. Career insights become typed nodes alongside intellectual
notes. Rejected: a separate career knowledge store.

## D009 — Promotion seam: CareerVinny stages, human types edges, KBAI ingests
CareerVinny writes a vault-shaped candidate to `state/promotions/`; the human
ratifies edges; KBAI's existing pipeline ingests. CareerVinny NEVER writes to the
vault directly. Transfer is lossy by design — most roles never become notes.

## D010 — Career notes: own folder AND domain tag
`02-career/` folder PLUS `domain: career` frontmatter tag — both, different jobs.
Edges cross folders freely; cross-domain links are the point.

## D011 — Dashboard: Claude Code, local, two panes, sequenced
Built by Claude Code (needs local FS). Pane B (graph health, read-only) first;
Pane A (promotion queue) later. Centrepiece: filtered career-subgraph + one-hop
neighbours. Rejected: one merged app; full-graph hairball.

## D013 — Mini Vinny is future vision, not MVP scope
Promotion seam, dashboard, interview-prep retrieval, generative "show what I know"
skill — all deferred. MVP is the CareerVinny pipeline only. Prove the substrate
first.

## D015 — Do NOT build scout on LinkedIn
LinkedIn is auth-walled, anti-scraping, locked API. Build scout on sources that
want to be read (ATS APIs, RSS, career pages). LinkedIn via Chrome connector ONLY
as last-mile auth-walled fetch for a specific already-found role.

## D016 — Generative "show what I know" skill needs a provenance gate (OPEN)
A skill drafting public-facing expertise claims must draw ONLY from settled-
conviction nodes, never the full graph. Gate mechanism undecided. Deferred; own
design conversation.

## D017 — Two learning loops, two files, two readers
ROLE loop = `reference/lessons.md` (+ lessons-audit.md; read by skills). DESIGN
loop = `design-lessons.md` (read by the designer). Never merge — different readers,
triggers, homes. The advisor-calibration lesson is a design-loop entry.

---

# ═══ BEDROCK (hardened into architecture.md; provenance only) ═══
One line each. Full reasoning in version history. Reopen only if a foundation is
genuinely challenged.

- **D001** — Folder layout split by who-reads / how-often-changes (reference/ ·
  state/ · inbound/ · skills/). Rejected flat repo.
- **D002** — Role = folder, not row. `state/roles/{company}-{role-slug}-
  {seniority}/`. Rejected single scored-roles table.
- **D003** — Seniority is part of the role key. Same role at two rungs = two
  folders; they score differently.
- **D004** — Gates stay tight; reach roles surface FLAGGED, not by loosening
  gates. "Aiming high" is presentation, not a gate decision.
- **D005** — inbound/ is transient, not an archive. JD passes through; permanent
  home is the role folder; inbound returns empty.
- **D006** — state/ is longitudinal, never garbage-collected. The score.md trail
  compounds over years; dashboard reads historically.
- **D007** — Three-tier memory model: ephemeral working context · transactional
  state/ · synthesised KBAI vault. Stateless = the AGENT holds nothing; files are
  not disposable.
- **D012** — Build tool division: Claude-in-chat = architect · Cowork = runtime ·
  Claude Code = operator infra · human = approve/ratify/submit.
  >> SUPERSEDED by D028 (2026-06-22): Cowork dropped — Claude Code is sole runtime + operator infra. <<

---

## CONTINUITY BUNDLE (attach to every new System Designer chat)
architecture.md · decisions.md · design-lessons.md · the spine files
(career-north-star, targets, fit-rubric, lessons + lessons-audit). Reconstructs
full design + career state. Skills are NOT in the bundle (Claude Code's, not the
designer's). Travelling docs (dashboard handoff, Mini Vinny risks) attach only
when that work resumes. For a fast start, LIVE tier + spine is usually enough;
SETTLED-ACTIVE and BEDROCK travel only when a settled question is reopened.
