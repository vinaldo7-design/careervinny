---
name: score-fit
description: Score one stored role (state/roles/{key}/jd.md) against the calibrated rubric into a state/roles/{key}/score.md — two axes (fit 0-100 + odds 0-1, never averaged), a band, and a MACHINE screen (reject/flag/pass). Use whenever a gate-passing role has been ingested and needs scoring: "score this role", "run score-fit", "how does this fit / what band". You supply one evidence-anchored judgment per rubric variable; a deterministic engine does the arithmetic. NOT for finding roles (that is discovery), NOT for converting a posting (that is ingest), NOT for drafting outreach (that is network) — and it NEVER writes the human verdict (pursue/on-ramp/no): that is logged gut-first into the ledger and must not be anchored by this file.
---

# score-fit — one jd.md → score.md

score-fit is the scorer at the end of the funnel: discovery lists, ingest converts, score-fit
scores the clean jd.md against the calibrated rubric. It produces a MACHINE screen — fit, odds,
band — and never a human verdict. The method is decomposed and evidence-anchored: one isolated
judgment per rubric variable (not a holistic "rate this 0-100"), each grounded in a verbatim
quote, then a fixed deterministic engine combines them. You bring the reading judgment; the
engine brings reproducible arithmetic and the audit trail.

## Procedure (one role per run)

1. **Gates first.** Read the `kind=gate` rows in `reference/fit-rubric.md` against the jd.md.
   If any hard gate fails (visa, London, £60k floor, strategic-not-IC, or an anti-fit
   disqualifier), the role is a reject — record which gate. Don't score a gated-out role.

2. **Extract one judgment per scoring variable.** For each non-gate row in the rubric table,
   read the jd.md and assign `{verdict: MET | PARTIAL | UNMET | CANNOT_ASSESS, quote, confidence}`,
   following that row's `how-to-read`. The `quote` MUST be a verbatim substring of the jd body —
   the engine string-matches it back and downgrades an unverifiable claim, so this is what stops
   you inventing a requirement. Use `CANNOT_ASSESS` when the JD is simply silent (never invent).
   Also capture: the two penalties (no-agency, frontier-free), comp (`stated_gbp` or null), the
   ESG×AI multiplier (fire only if responsible-AI / AI-governance / AI-ethics / AI-sustainability
   is genuinely the role, not boilerplate), prestige, the candidate odds factors from
   `reference/odds-rubric.md` (seniority_match × requirement_match × competition), and the agency
   guard. (Recency is computed by the engine from jd.md's `posting-age` — you don't set it.) Write
   it to `state/roles/{key}/extraction.json`.

3. **Run the engine.** `python3 skills/score-fit/scripts/scorer.py --role {key}`. It evidence-
   gates every quote, applies the spine floor-gate (D023), the normalised weighted sum, penalties,
   the comp curve, and the ESG×AI multiplier in one fixed order; computes odds as an
   anti-compensatory product and the band (D019); and writes `score.md` stamped with
   `rubric-version` and a body that cites every fired row. The engine is dumb and fixed — it
   hardcodes no variable; it iterates the table.

4. **Do not surface the score before the gut verdict.** score.md's `verdict:` field stays empty.
   The human logs pursue/on-ramp/no gut-first into the calibration ledger; showing the machine
   score first would anchor that label (CLAUDE.md). The machine field is `screen:`, never `verdict:`.

## Adapting the rubric (why this is modular — D024)

Weights, floors, and the variable list live as DATA in `reference/fit-rubric.md`'s table. Add a
variable = add a row; disable one = set its weight to 0; shift a preference = change a weight (the
engine re-normalises, so prior scores don't rebase). New spine trait = add a `kind=spine` row with
a floor. You never edit `scorer.py` to change what's valued — only the table. A genuinely new kind
of math is the only thing that touches code. The rubric already absorbs the accepted lessons
(L002–L009 backported into the table); read it as the live source. `status:watch` deltas (e.g.
L006 networkability) are deliberately NOT applied yet.

After ANY rubric or engine edit, run `scripts/check.sh` — it runs the engine fixtures plus the
calibration-ledger regression guard (`ledger_check.py`), which goes red if an edit makes the
machine contradict an already-decided role (a logged human verdict) by more than one band.

## A note on the two axes

fit ("do I want it") and odds ("can I get it") never collapse into one number (D018). odds is a
product, so any near-zero factor sinks it — correct, because you cannot get a role you are three
rungs too junior for. At v0 the `competition` factor is a low-confidence placeholder, so odds is directional, not
decision-grade — say so. Recency is NOT in odds: a posting older than `STALE_DAYS` (42) is held
out of banding (band null) and flagged `likely-closed:verify-live`. Prestige does not multiply
fit; it routes the band
(high-fit + low-odds + prestige → moonshot, network-first).

## Done when

`state/roles/{key}/score.md` exists with fit + odds + band + screen + `rubric-version`, a body
that cites the specific rubric rows (with evidence quotes) behind the number, and `verdict:` left
empty. score-fit reads `reference/` (fit-rubric, odds-rubric) and the role's `jd.md` only — never
`docs/` — and writes only into `state/roles/{key}/`.
