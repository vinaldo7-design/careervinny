---
name: odds-rubric
description: The attainability (odds) model for score-fit — the SECOND axis (D018), never averaged with fit. odds = seniority_match × requirement_match (anti-compensatory product, D018). Lives in score-fit's read path. Competition was dropped — it can't be measured without market data.
rubric-version: 2
status: v2, 2026-06-24 (competition dropped — unmeasurable; odds = seniority × requirement)
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

(Competition was DROPPED 2026-06-24: how-contested can't be measured without market data, and a
fabricated 0.5 placeholder just halved every odds for no signal. odds is now the two factors
that ARE readable from the JD + profile.)

## Conventions (machine)
- **odds = seniority_match × requirement_match**, each in [0,1]; result in [0,1].
- **odds-confidence:** low while the two factors are uncalibrated judgment reads; raise as grounded.
- A near-zero factor collapses odds — that is the point (anti-compensatory).
- odds carries a date-stamp on every score.md; fit does not (D018 decay asymmetry).
- **Recency is NOT an odds factor.** A posting older than score-fit's `STALE_DAYS` (42) is treated
  as likely-closed: held out of banding (band null) + flagged `likely-closed:verify-live`, rather
  than decaying odds. Freshness is a still-open question, not a smooth attainability gradient.

## Band coupling (D019)
The band (safety / achievable / stretch / moonshot) is a function of (fit, odds) computed by
score-fit per fit-rubric.md's band logic; odds is the reachability axis that sorts wanted
roles. Networking raises odds and re-bands a role upward (D020).
