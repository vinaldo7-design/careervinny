---
name: calibration-ledger
description: The compounding calibration record for CareerVinny scoring. One row per real role scored, with Vinay's verdict + one-line why + the GAP between his verdict and the rubric's provisional band. The accumulated GAP column is what weights get fitted to (D025 Phase 2). Below the ledger: extrapolated lessons (generalised L-series deltas). This is the labelled dataset that turns guessed weights into calibrated ones.
status: v1, seeded with the first 5 verdicts (2026-06-19)
---

# CareerVinny — Calibration Ledger

## How to read
- **verdict**: pursue / on-ramp / no (Vinay's call, made BEFORE seeing the rubric score — gut first, to avoid anchoring)
- **why**: Vinay's own words, compressed
- **provisional band**: what the CURRENT rubric would have scored it (high/med/low fit)
- **GAP**: did the verdict match the band? Where verdict ≠ rubric, that divergence is the calibration signal. "match" = no signal; a divergence = a weight to move.

## Ledger

| # | role | verdict | why (Vinay's words) | rubric band | GAP |
|---|------|---------|---------------------|-------------|-----|
| 1 | Accenture — Tech Strategy Mgr, FS | pursue (strong) | "frontier AI strategy + C-suite + the client-facing/origination I want and don't have" | high | match — but revealed client-facing & origination were UNDER-weighted (rubric had them minor). Verdict right, weights wrong → L002/L003 |
| 2 | Capco — Data & AI Strategist | pursue (strong) | "shape C-suite AI ambitions, lead strategy definition, my EU-AI-Act edge; don't care it's not super-prestigious if stable + large" | high (IF prestige-gated: would've been docked) | DIVERGENCE — rubric prestige near-gate would have penalised a non-marquee firm; verdict says prestige shouldn't gate → L004 (prestige→multiplier). Also rung: would enter Senior Consultant → L005 |
| 3 | JPMorgan — Strategy Sr Assoc, AI Enablement | on-ramp (pursue) | "step down in agency but a good on-ramp, prestige, London, I can network in, assess AI tools which Oxford taught me; like strategy+hands-on but not running tools/tech-support" | med (agency scoped) | match-ish — wanted via ATTAINABILITY not fit (D018 working). Watch: on-ramp must not become license for low-agency-for-prestige → L007 |
| 4 | Deloitte — AI & Data Delivery | no (hard) | "very technically focused, that tech stack is not what I want, hell no" | low (IC-tell fires) | match — IC-tell gate correct. Build-stack = reject, confirmed by strong negative → L008 |
| 5 | EY-Parthenon — Asst Director, Tech S&E | no (boring) | "M&A due diligence sounds boring; I don't want roles just for prestige or client-facing that don't excite me" | med (prestige+client-facing high, frontier absent) | DIVERGENCE the RIGHT way — rubric might have ranked it med on prestige+client-facing; verdict says frontier-free work fails regardless → L009 confirms frontier spine still bites after L002/L004 loosening |

## Extrapolated lessons (generalised from the deltas — the real calibration output)

**The headline finding:** the interview over-weighted STATUS (prestige-as-gate, rung-protection) and under-weighted TEXTURE (client-facing, being-in-the-room, playing with AI tools). The one variable that predicted all 5 verdicts correctly: **"does the WORK excite me — frontier-AI strategy where my judgment shapes things and my ESG×AI edge counts."** That is the real spine. Everything else is texture around it.

- **L002** client-facing: supporting (~3pts) → HEAVY weight (revealed want, not minor).
- **L003** origination/BD: repulsion → WANTED, but only bundled with strategy-setting (relationship+pitch ownership yes; revenue-quota/number ownership still repels). Guard: pure-sales-no-strategy still fails.
- **L004** prestige: near-gate (−30) → POSITIVE MULTIPLIER. Real gate underneath = FIRM STABILITY + SIZE + SECURITY. High-prestige+high-fit+low-reach → moonshot/network bucket, never killed.
- **L005** seniority drift-guard: fires on WORK CONTENT, not title string. Rung-down at a fit firm with strategy-grade work = on-ramp, not penalty.
- **L006** networkability: WATCH — possible distinct fit signal or just client-facing re-described. Test in the 200-batch via the networkability field.
- **L007** attainability band confirmed (D018): take the gettable on-ramp, not only moonshots. Watch: on-ramp ≠ buying the logo with autonomy.
- **L008** IC-tell gate correct: named build-stack-as-requirement = reject. The line is BUILD vs ASSESS — Vinay wants to evaluate tools, not engineer them.
- **L009** frontier-AI spine floor still bites after L002/L004: prestige + client-facing are multipliers that tune ranking, NOT rescuers that resurrect frontier-free work. "Boring" = frontier/edge content absent.

## Next calibration target
~30-50 verdicts from the 200-batch. At that volume, fit the weights to the GAP
column (D025 Phase 2) — until then, find signals, don't over-tune on small N.
