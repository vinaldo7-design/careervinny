---
name: fit-rubric
description: Scoring logic for score-fit. Shared reference, read by many, owned by none. Projects from career-north-star.md via targets.md. Produces a 0-100 fit score + confidence flags + anti-fit verdict. Roles failing a hard gate never reach scoring. CALIBRATED 2026-06-19 against 5 real roles (L002-L009); comp re-keyed to floor+penalty curve.
status: v2, calibrated against first 5 real verdicts (2026-06-19)
---

# Fit Rubric (v2 — calibrated)

## What changed in v2 (from real-role calibration, see lessons.md L002-L009)
- Prestige: near-gate (−30) → POSITIVE MULTIPLIER. Real gate underneath = firm
  stability + size + security (L004).
- Client-facing: supporting (~3pts) → HEAVY weight (L002).
- Origination/BD: repulsion → WANTED when bundled with strategy-setting (L003).
- Seniority drift-guard: fires on WORK CONTENT, not title string (L005).
- Comp: hard £100k gate → £60k floor + graduated penalty curve (this version).
- Frontier-AI spine floor CONFIRMED still binding after the above loosening (L009).
- IC-tell gate CONFIRMED correct: build-stack = reject (L008).
- The real spine, revealed: "does the WORK excite me — frontier-AI strategy where
  my judgment shapes things and my ESG×AI edge counts." Everything else is texture.

## Pipeline order (cheap gates before expensive scoring)
1. Hard eligibility gates (boolean) → fail any = reject, do not score.
2. Anti-fit disqualifiers → fail any = reject, do not score.
3. Weighted fit score (0-100) on survivors.
4. Anti-fit penalties (non-disqualifying) subtract, incl. comp curve.
5. Prestige + ESG×AI multipliers apply.
6. Confidence flags + guards attached to the briefing line.

## 1. HARD ELIGIBILITY GATES (boolean — fail = auto-reject)
These are physics, not preference. A role failing these cannot be accepted.
- **Visa sponsorship** (see §VISA — register lookup; 3-outcome logic).
- **London / London-anchored / UK hybrid.** Non-UK or remote-outside-UK = reject.
- **Comp floor: £60k base GBP.** Below £60k stated = reject (below-market for rung;
  fit sinks these anyway — floor is a cheap cut, the CURVE does the real work, §4).
- **Strategic, not IC-engineering** (see §IC TELLS).

## 2. ANTI-FIT — DISQUALIFIERS (repulsion, not mere absence of fit)
- **Production-code IC role** (FDE-as-coding-job, ML eng, SWE) — see IC tells.
  CONFIRMED L008: named build-stack as hard requirement = reject (Deloitte).
- **Founder-load / outcome-ownership** as core mandate ("own whether this works",
  "first hire", "build the function from zero", startup-CTO-shaped). NOTE L003:
  this is REVENUE-NUMBER ownership, NOT relationship/pitch ownership (which is wanted).
- **Pure terminal-IC track** with no reports and no management path (oracle trap).
- **Pure sales / revenue-quota-carrying** with NO strategy mandate (L003 guard).

## 2b. ANTI-FIT — PENALTIES (subtract from score, don't disqualify)
- **No-agency / powerlessness**: "support the team", "execute the partner's plan",
  pure delivery verbs, no shaping room → −15 to −25. (L001: penalise POWERLESSNESS,
  not deliverable-type. Decks/training/enablement = neutral if judgment-bearing.)
- **Prestigious-but-dull / frontier-free**: cost-takeout, rebadged "digital
  transformation", M&A tech-diligence, no named frontier tech → −20. CONFIRMED L009:
  prestige + client-facing do NOT rescue this (EY-Parthenon reject). The frontier-AI
  spine floor still bites.
- **Strategy-absorbed-into-delivery** (verify-live, low-confidence): title says
  strategy but role executes a frame leadership pre-set. JD can't reveal — verify
  via Glassdoor/contact. Flag "agency: absorbed-risk, verify live".
- **Comp curve** — see §4. Graduated, not a gate above £60k.

## 3. PRESTIGE — now a MULTIPLIER, not a gate (L004)
- Prestige is a POSITIVE BOOSTER (marquee name lifts a role) — NOT a floor.
  Its absence no longer sinks a role.
- The REAL gate prestige stood in for: **firm stability + size + job security.**
  Successful + large enough to be secure = pass. Sub-Series-C / shaky / too-small
  = fails (this keeps the protective job the old prestige gate did).
- ROUTING: high-prestige + high-fit + low-reachability → MOONSHOT/networking
  target (D019), never gated out. Prestige is multiplier AND band-router, never a kill.

## 4. WEIGHTED FIT SCORE (0-100 across survivors)

### Co-dominant spine — ~50 pts combined (each has a FLOOR-gate, D023)
**Frontier tech-domain strategy (~30 pts)** — THE confirmed spine (L009). Score
from observable proxies: named frontier tech in responsibilities (agentic/LLM/RAG/
named model = high; vague "AI/ML" = low); who you advise (C-suite/board > stake-
holders > internal); work verb (design/architect/shape/set > support/enable >
execute/maintain); team novelty; client type. Flag frontier-confidence high/med/low.
**Management ladder (~20 pts)** — legible rungs, reports reachable 2-3 yrs.
Flag ladder: confirmed/inferred/absent. Tiebreak: frontier wins among prestige opts.

### Heavy — ~38 pts (client-facing promoted, L002)
- Intellectual agency (~12) — judgment shapes work. Flag "agency: verify live".
- **Client-facing (~10) — PROMOTED from ~3 (L002).** Client/customer-facing,
  workshops, C-suite relationships, being-in-the-room. A revealed heavy want, not
  minor. Travel/road-warrior bundled here = plus.
- Player-coach design (~8) — craft + small team now.
- Peer-bar / intensity (~8) — elite peers, stretched-by-room.

### Supporting — ~12 pts
- **Origination / BD (~6) — RE-KEYED from repulsion (L003).** Owns relationship +
  pitch + SoW = WANTED, but ONLY when bundled with strategy-setting. Pure-sales /
  revenue-quota with no strategy = disqualifier (§2), not a plus.
- Job security / firm stability. Industry: neutral.

### COMP CURVE (graduated penalty — never a fit BOOST)
Comp NEVER adds to fit (a higher salary does not make the WORK more wanted — that
keeps money from rescuing roles the work should kill). It only removes a penalty as
pay rises:
- < £60k (stated) → HARD KILL (gate §1).
- £60k → −20  |  £70k → −15  |  £80k → −10  |  £90k → −5  |  £100k+ → 0.
  Linear between steps. Penalty shrinks every £10k; zero at £100k+.
- Unstated comp → NO penalty, FLAG it (don't punish a hidden number; confirm in screen).
- Effect: a £75k role outscores an equal £65k role (smaller dent) — the "each 10k
  up is better" feel — WITHOUT comp ever boosting a role above its work-fit ceiling.

## 5. BONUS MULTIPLIERS (applied after base score)
- **ESG × AI co-occurrence ×1.25** (cap 100). Responsible-AI / AI-governance /
  AI-ethics / AI-sustainability genuinely present. Highest-leverage edge.
- **Prestige multiplier** (L004): marquee name lifts the ranked score (does not gate).

## VISA — 3-outcome gate (register lookup)
- **On Register of Licensed Sponsors** (gov.uk CSV, fuzzy-matched) → PASS.
- **Not on register + small/unknown firm** → REJECT.
- **Not on register + large multinational** (likely licensed under variant name) →
  FLAG, do not reject (name-match false-negatives are the costly error).
- Register membership necessary, not sufficient (licensed ≠ will sponsor THIS role).

## IC TELLS (fail the strategic-not-IC gate on disguised roles)
Reject when: coding languages/infra as HARD requirements (Python/TS/SQL/Spark/K8s/
Docker as must-haves); deliverable is "production code"/"pipelines"/"ship systems";
"startup-CTO-shaped"/"roll up sleeves and build". CONFIRMED L008 (Deloitte: SQL/
Python/Spark/Hadoop/AWS = reject). The line is BUILD vs ASSESS — evaluating AI tools
(wanted, JPM) is NOT building them (rejected, Deloitte).

## GUARDS (attach to briefing, don't alter fit score)
- **Recency**: flag if >8 weeks old / repost / ghost.
- **Seniority drift (CONTENT-keyed, not title, L005)**: judge rung by years +
  comp-band + reports/scope, NEVER the title string. Map by industry: VP@bank ≈
  Manager@consultancy ≈ Lead/Strategist@lab ≈ Senior-Associate@MBB ≈ entry rung.
  Drift-DOWN at a fit firm with strategy-grade work = valid ON-RAMP, not penalty.
  Fire only on genuine content mismatch or mis-pitch-UP (titled far above rung).
- **Networkability (WATCH, L006)**: is a role-relevant human reachable? Possibly a
  fit signal, possibly client-facing re-described. Flag, don't weight yet.

## LEARNING LOOP
Real verdicts + accept/decline write to lessons.md and backport HERE — especially
anti-fit (§2/§2b). Calibration ledger accumulates the GAP between verdict and band;
at ~30-50 verdicts, fit the weights to the GAP column (D025 Phase 2). This file is
the substrate's memory of what real roles proved, not what was said up front.
