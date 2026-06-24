---
name: odds-rubric
description: The attainability (odds) model for score-fit — the SECOND axis (D018), never averaged with fit. odds = seniority_match × requirement_match × competition (anti-compensatory product, D023). Lives in score-fit's read path. v0: requirement_match from profile↔jd, competition is a low-confidence placeholder.
rubric-version: 1
status: v1, 2026-06-24 (competition factor least-grounded — refine from real roles, D025)
---

# Odds rubric (attainability)

odds is the second axis (D018): "can I GET this", never collapsed into fit. It is an
ANTI-COMPENSATORY PRODUCT (D023) — any near-zero factor collapses the result, because you
cannot get a role you are three rungs too junior for, however well you match everything
else. Date-stamped on every score (odds moves as Vinay ships / publishes / warms a contact;
fit does not).

## Factors (machine — read by scorer.py)
| id | factor | how-to-read |
|----|--------|-------------|
| seniority_match | Seniority match | 1.0 if the role's CONTENT-rung (years + comp-band + reports, NOT the title string) sits at Vinay's entry rung (Consultant/Manager/Lead/Strategist, ~5 yrs); 0.5 a rung off; 0.2 two-plus rungs off. Drift-DOWN at a fit firm with strategy-grade work is a valid on-ramp — score ~0.8, not a penalty (L005). |
| requirement_match | Requirement match | Fraction of the role's hard requirements Vinay's master-profile.md can evidence (CS+DS degrees, Oxford AI dip, HPE AI/ESG build + assurance, LLM/agentic, stakeholder/exec comms). 1.0 most met, 0.5 about half, 0.2 few. v0: read the JD requirements against master-profile blocks. |
| competition | Competition | How contested the role is. v0 PLACEHOLDER = 0.5 (low-confidence) — least-grounded factor (D023), refine from real roles during calibration. |
| recency | Posting freshness | Auto-computed by the engine from jd.md `posting-age` (NOT judged by the extractor). A fresh posting is more gettable (likelier still open, earlier in the pipeline); an old one less so. See §Recency curve. |

## Conventions (machine)
- **odds = seniority_match × requirement_match × competition × recency**, each in [0,1]; result in [0,1].
- **odds-confidence:** low while competition is the 0.5 placeholder; raise as factors are grounded.
- A near-zero factor collapses odds — that is the point (anti-compensatory).
- odds carries a date-stamp on every score.md; fit does not (D018 decay asymmetry). Recency is
  WHY odds decays over time: the same role posted long ago is less gettable, so it sinks toward
  the lower bands (stretch/moonshot) while fresh roles rise (safety/achievable). Recency NEVER
  touches fit — the work does not worsen with posting age.

## Recency curve (machine)
Posting age (days, from jd.md `posting-age`) → an odds multiplier; linear between breakpoints.
Gentle, with a 2-week grace, reaching the full penalty at 8 weeks (tunable as data, D025):
- 14 → 1.0
- 56 → 0.55

(≤14 days = fresh, ×1.0; ≥56 days = ×0.55 floor. Unknown posting-age → ×1.0, flagged.)

## Band coupling (D019)
The band (safety / achievable / stretch / moonshot) is a function of (fit, odds) computed by
score-fit per fit-rubric.md's band logic; odds is the reachability axis that sorts wanted
roles. Networking raises odds and re-bands a role upward (D020).
