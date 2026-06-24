---
name: fit-rubric
description: Scoring logic for score-fit. Shared reference, read by many, owned by none. Projects from career-north-star.md via targets.md. Produces a 0-100 fit score + confidence flags + a machine screen (reject/flag/pass) — NEVER a human verdict. Roles failing a hard gate never reach scoring. CALIBRATED 2026-06-19 against 5 real roles (L002-L009); v3 re-expresses the calibrated weights as a machine-iterable variable table with numeric floors (D024).
rubric-version: 3
status: v3, 2026-06-24 (v2 calibration re-expressed as a machine table + numeric spine floors; weights unchanged in meaning)
---

# Fit Rubric (v3 — calibrated weights as a machine table)

The WEIGHTS and FLOORS now live in the **variable table** below — one row per variable,
each with weight, floor, kind, and how-to-read (D024). The score-fit engine iterates the
rows; it hardcodes no variable name. Add a variable = add a row; disable = weight 0; shift
preference = change a weight. The prose under the table is the calibrated RATIONALE (the
L00x deltas), kept human-readable; the table is what the engine reads.

## What changed in v2/v3 (from real-role calibration, see lessons.md L002-L009)
- Prestige: near-gate (−30) → POSITIVE band-router (L004). Real gate underneath = firm
  stability + size + security (the `firm-stability` row).
- Client-facing: supporting (~3pts) → HEAVY weight (L002).
- Origination/BD: repulsion → WANTED when bundled with strategy-setting (L003).
- Seniority drift-guard: fires on WORK CONTENT, not title string (L005) — now an odds factor.
- Comp: hard £100k gate → £60k floor + graduated penalty curve (D026).
- Frontier-AI spine floor CONFIRMED still binding after the above loosening (L009).
- IC-tell gate CONFIRMED correct: build-stack = reject (L008).
- v3: every weight is now an exact integer summing to 100, every spine trait has a numeric
  floor (0.4), and prestige moved off the fit axis to the band router (was an undefined-
  magnitude multiplier). The v2 WEIGHTS are unchanged; the numeric spine floors are NEW (the
  floor-gate was prose-asserted but uncomputable before v3) — so the gate now bites where it
  previously couldn't.
- The real spine, revealed: "does the WORK excite me — frontier-AI strategy where my
  judgment shapes things and my ESG×AI edge counts." Everything else is texture.

## Pipeline order (cheap gates before expensive scoring)
1. Hard eligibility + anti-fit gates (kind=gate) → fail any = screen:reject, do not score.
2. Per-variable evidence-gated extraction on survivors (one judgment per row).
3. Weighted fit (0-100) over the additive rows (spine + heavy + supporting).
4. Spine floor-gate (D023); penalties; comp curve; ESG×AI multiplier — in the fixed order below.
5. Odds (separate axis — see odds-rubric.md) + band (D019).
6. Confidence flags + guards attached to the score.md body.

## Scoring conventions (machine — read by score-fit/scripts/scorer.py)
- **Enum → value:** MET = 1.0, PARTIAL = 0.5, UNMET = 0.0. CANNOT_ASSESS = abstain.
- **Abstention:** CANNOT_ASSESS on a non-spine row is excluded from BOTH numerator and
  denominator (and recorded); on a SPINE row it counts as a floor breach (you cannot
  confirm the spine) — flag it, never silently drop a 30-pt variable.
- **Fit (normalised, 0-100):** fit_base = round(100 × Σ(value×weight) ÷ Σ(weight)) over the
  ASSESSED additive rows. Normalising by the assessed-weight sum means editing or disabling
  a weight is a local change that never rebases prior scores.
- **Spine floor-gate (D023):** if either spine row's value < its floor (0.4), the role is
  flagged spine-floor:breached and falls below the bar — no band, screen:reject — regardless
  of fit_base. The two co-dominant spine traits "must each clear a minimum before the sum
  counts" (D023 anti-lopsidedness): a near-zero frontier or ladder is not bought back by the rest.
- **Order of operations (one fixed order, single final clamp):** fit_base → minus penalties
  that fired → minus comp-curve → × ESG×AI multiplier (if MET) → clamp to [0, 100].
- **Prestige** is a band-router, not a fit multiplier (v0) — it only moves the band.
- **screen (machine pre-screen, NOT the human verdict):** reject = a gate failed; flag =
  passed gates but has a concern (spine-floor breached, fit below ~50, agency verify-live,
  recency stale, or a spine CANNOT_ASSESS); pass = clean and high-fit. The human verdict
  (pursue/on-ramp/no) is logged gut-first into the ledger and is NEVER written here.
- **rubric-version:** this file's frontmatter `rubric-version` is stamped onto every
  score.md; only same-version scores are comparable (D025).

## Variable table (machine)
| id | variable | kind | weight | floor | how-to-read |
|----|----------|------|--------|-------|-------------|
| visa-sponsorship | UK visa sponsorship | gate | — | — | On UK sponsor register PASS; not-on-register and small/unknown REJECT; not-on-register and large multinational FLAG. See §VISA. |
| location-uk | London / UK-anchored | gate | — | — | London, London-anchored, or UK hybrid PASS; non-UK or remote-outside-UK REJECT. |
| comp-floor | Comp floor £60k | gate | — | — | Stated base below £60k GBP REJECT (D026); at or above passes to the comp-curve penalty. |
| strategic-not-ic | Strategic, not IC | gate | — | — | Coding stack as hard requirement, production-code deliverable, or build/deploy verbs REJECT. The line is BUILD vs ASSESS. See §IC TELLS. |
| disq-production-ic | Production-code IC role | gate | — | — | FDE-as-coding-job, ML engineer, SWE REJECT (anti-fit disqualifier). |
| disq-founder-load | Founder-load / outcome-ownership | gate | — | — | Owning whether the bet works, revenue-number ownership, first-hire, startup-CTO-shaped REJECT. NOT relationship/pitch ownership, which is wanted (L003). |
| disq-terminal-ic | Pure terminal-IC track | gate | — | — | No reports and no management path, oracle trap REJECT. |
| disq-pure-sales | Pure sales / quota | gate | — | — | Revenue-quota-carrying with NO strategy mandate REJECT (L003 guard). |
| frontier-strategy | Frontier tech-domain strategy | spine | 30 | 0.4 | Named frontier tech in responsibilities (agentic, LLM, RAG, named model) MET; vague "AI/ML" PARTIAL; none UNMET. Lift by who you advise (C-suite over stakeholders over internal) and work verb (design/shape/set over support over execute). THE spine (L009). |
| mgmt-ladder | Management ladder | spine | 20 | 0.4 | Legible rungs with reports reachable in 2-3 yrs MET; inferred PARTIAL; absent UNMET. |
| intellectual-agency | Intellectual agency | heavy | 12 | — | Judgment shapes the work MET; scoped-but-real PARTIAL; execution-only or powerlessness UNMET. Verify live (L001). |
| client-facing | Client-facing | heavy | 10 | — | Client/customer-facing, workshops, C-suite rooms, road-warrior travel MET. A revealed heavy want (L002). |
| player-coach | Player-coach design | heavy | 8 | — | Craft now plus a small team now MET. |
| peer-bar | Peer-bar / intensity | heavy | 8 | — | Elite peers, stretched-by-the-room MET. |
| origination-bd | Origination / BD | supporting | 6 | — | Owns relationship, pitch, SoW bundled WITH strategy-setting MET (L003); pure sales is a disqualifier, not scored here. |
| firm-stability | Firm stability / security | supporting | 6 | — | Successful and large enough to be secure MET; sub-Series-C, shaky, too-small UNMET. The real gate prestige stood for (L004). |
| pen-no-agency | No-agency / powerlessness | penalty | -20 | — | Fixed-plan execution, no shaping room, pure delivery verbs → subtract (L001). Range -15..-25, use -20. |
| pen-frontier-free | Prestigious-but-dull | penalty | -20 | — | Cost-takeout, rebadged digital transformation, M&A diligence, no named frontier → subtract (L009). Usually co-fires with a spine-floor breach. |
| comp-curve | Comp curve | comp-curve | — | — | Graduated penalty by stated base; see §Comp curve (machine). Never boosts; unstated = 0 and flag. |
| mult-esg-ai | ESG × AI | multiplier | 1.25 | — | Responsible-AI / AI-governance / AI-ethics / AI-sustainability genuinely present → multiply fit by 1.25 (cap 100). Highest-leverage edge. |
| mult-prestige | Prestige | band-router | — | — | Marquee name does NOT multiply fit (v0); it routes the band — high-fit + low-odds + prestige → moonshot (L004, D019). |

(additive weights: spine 30+20=50, heavy 12+10+8+8=38, supporting 6+6=12 → total 100.)

## Comp curve (machine)
Stated base (GBP) → fit penalty, linear between breakpoints; unstated → 0 (flag):
- 60000 → -20
- 70000 → -15
- 80000 → -10
- 90000 → -5
- 100000 → 0

(below 60000 is the hard gate `comp-floor`, not a curve point.)

## Band (machine, D019 — v1 heuristic, tunable as data)
A disjoint partition of (fit, odds) for roles that cleared the gates AND the spine floor-gate:
- fit ≥ 70 and odds ≥ 0.5 → safety
- fit ≥ 70 and 0.25 ≤ odds < 0.5 → achievable
- fit ≥ 70 and odds < 0.25 → stretch
- 50 ≤ fit < 70 → achievable if odds ≥ 0.5 else stretch
- prestige band-router: high-fit + odds < 0.25 + prestige → moonshot (never gated out)
- fit < 50 → no band; screen:reject (a wanted role never sits below the bar). A spine-floor
  breach also lands here — see the floor-gate convention above.

When odds-confidence is low (the v0 competition placeholder), the band is stamped *provisional*.
Thresholds are v1 hypotheses (D025), changed as data — not engine — edits.

---

# Calibrated rationale (prose — the WHY behind the rows)

## Hard gates are physics, not preference
A role failing visa / London / £60k-floor / strategic-not-IC cannot be accepted. The
comp floor is a cheap cut; the CURVE does the real ranking work above £60k. IC-tell: the
line is BUILD vs ASSESS — evaluating AI tools (wanted, JPM) is NOT building them (rejected,
Deloitte L008).

## Anti-fit disqualifiers (repulsion, not mere absence of fit)
Production-code IC; founder-load / revenue-number ownership (NOT relationship/pitch
ownership, which is wanted, L003); pure terminal-IC (oracle trap); pure sales with no
strategy mandate. These are gates, not penalties.

## Penalties (subtract, don't disqualify)
- **No-agency / powerlessness** (L001): penalise POWERLESSNESS — fixed-plan execution, no
  shaping room — NOT deliverable-type. Decks/training/enablement are neutral if judgment-bearing.
- **Prestigious-but-dull / frontier-free** (L009): cost-takeout, rebadged digital
  transformation, M&A tech-diligence with no named frontier. Prestige + client-facing do
  NOT rescue this — the frontier spine floor still bites (EY-Parthenon reject).

## The co-dominant spine (~50 pts, each floor-gated, D023)
Frontier tech-domain strategy (30) is THE confirmed spine (L009): score from observable
proxies — named frontier tech, who you advise, the work verb, team novelty, client type.
Management ladder (20): legible rungs, reports reachable 2-3 yrs. Tiebreak: frontier wins
among already-prestige options. The floor-gate stops a role huge on one spine trait and
near-zero on the other from climbing on imbalance.

## ESG × AI multiplier (×1.25) — the highest-leverage edge
Responsible-AI / AI-governance / AI-ethics / AI-sustainability genuinely present. Rare,
high-conversion; must not be buried by generic AI.

## §VISA — 3-outcome gate (register lookup)
On Register of Licensed Sponsors (gov.uk CSV, fuzzy-matched) → PASS. Not on register +
small/unknown → REJECT. Not on register + large multinational (likely licensed under a
variant name) → FLAG, do not reject (false-negatives are the costly error). Register
membership is necessary, not sufficient.

## §IC TELLS — fail the strategic-not-IC gate on disguised roles
Reject when coding languages/infra are HARD requirements (Python/TS/SQL/Spark/K8s/Docker
as must-haves); the deliverable is "production code"/"pipelines"/"ship systems";
"startup-CTO-shaped"/"roll up sleeves and build". CONFIRMED L008 (Deloitte: SQL/Python/
Spark/Hadoop/AWS = reject).

## §GUARDS (attach to the score.md body; do not alter the fit number)
- **Recency:** flag if > 8 weeks old / repost / ghost.
- **Seniority drift (CONTENT-keyed, not title, L005):** judge rung by years + comp-band +
  reports/scope, NEVER the title string. Drift-DOWN at a fit firm with strategy-grade work
  is a valid ON-RAMP — now scored on the odds `seniority_match` factor, not penalised.
- **Networkability (WATCH, L006):** flag, don't weight yet.

## Learning loop
Real verdicts + accept/decline write to lessons.md and backport into this table —
especially anti-fit. The calibration ledger accumulates the GAP between verdict and band;
at ~30-50 verdicts, fit the weights to the GAP column (D025 Phase 2). Until then the
weights are v1 hypotheses — change the data, never the engine.
