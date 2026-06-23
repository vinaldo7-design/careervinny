# CLAUDE.md — CareerVinny executor

## What this is
This repo scores job roles against Vinay's calibrated career preferences and
stages outreach. It FINDS and STAGES; Vinay DECIDES and SENDS. You are the
executor: you do the mechanical work, never the judgment and never the sending.

This repo is the only source of truth. Nothing outside it overrides what's on disk.

## How you work
- Build down `docs/STATUS.md`: take the topmost `next` scope, finish it end to end.
  A scope is done when it PROVES its stated claim — that claim is your test.
- A design question that surfaces mid-task: append it to `docs/decisions.md` as an
  open Q. Do not resolve it inline. Do not reopen a settled decision.
- Commit after each session; the message names what changed.

## Hard constraints (these never relax)
- Never send, submit, apply, or email. (The withheld tool is the real guarantee.)
- Never invent a verdict. Verdicts are handed in from a thinking session; you only
  log them. Never audit your own log — that's a separate fresh session's job.
- `calibration-ledger.md` is append-only. Never rewrite a past row.
- Rubric → script is one-directional. The script reads weights; it never writes them.
- Never fabricate a field. Missing data → "not stated". Bad data poisons calibration.
- Gate on role CONTENT, never on a token — brand, title string, single firm (DL005).
- Claims about how a tool or system BEHAVES are flagged or checked, never asserted
  as fact (DL001).

## Reading discipline
Open the file a rule lives in; this file points, it never duplicates (duplicates
go stale). Skills read `reference/` and write `state/`. Skills NEVER open `docs/` —
that's human and executor planning only. You read `docs/STATUS.md` and
`docs/decisions.md` to know what to build; the skills you write do not.

## Stale — never read
`CAREERVINNY-BRIEF.md`, `CAREERVINNY-FULL-CONTEXT.md`. Superseded by the spine.
