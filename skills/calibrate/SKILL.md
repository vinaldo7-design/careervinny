---
name: calibrate
description: Open a local clickable dashboard that walks through scored roles one at a time — JD + gates + per-variable extraction first, gut verdict + one-line reason second, machine score revealed third. Use whenever you want to label roles to calibrate the rubric: "calibrate", "run the dashboard", "let me label some roles", "review the calibration". Every click appends to calibration-ledger.md AND calibration-log.jsonl, never rewriting a past row. NOT for finding roles (discovery), ingesting (ingest), or scoring (score-fit) — this skill is the human-in-the-loop labeller that calibrates the others.
---

# calibrate — the labelling dashboard

calibrate is how a human gut verdict becomes calibration data. It enforces two rules
mechanically that prose alone cannot: the machine score is held back until the verdict is
logged (anti-anchoring), and every verdict appends a new ledger row (never rewrites).

## Procedure

1. **Run the server:** `bash skills/calibrate/scripts/run.sh` — runs guards (check.sh +
   pure-fn tests) then opens `http://127.0.0.1:8765`. Click roles in the queue; you see the
   JD link + gates + variables with HIT/MISS pills. Score is NOT on the page yet.
2. **Log your verdict:** click pursue / on-ramp / no, type one line, submit. The server
   appends to `calibration-ledger.md` and `calibration-log.jsonl` with the live
   `rubric-version`.
3. **Read the reveal:** the page reloads showing the score, the band, and the divergence
   between your verdict band and the machine's. Move to the next role.
4. **After each batch of ~20 verdicts**, run `python3 skills/calibrate/scripts/review.py` — it scans the log
   and writes new `status: proposed` deltas to `reference/lessons.md`. You ratify deltas →
   edit the rubric → re-run `skills/score-fit/scripts/check.sh` (must stay green) → next batch.

## A note on what the dashboard MUST NOT do

It must not write your verdict. It must not change the rubric. It must not show the score
before the verdict is logged. Gate changes go via lessons.md proposals; they never auto-apply.

## Done when

`calibration-log.jsonl` carries one JSON row per labelled role; `calibration-ledger.md` has a
matching markdown row with `key:<role-key>`; the ledger guard
(`skills/score-fit/scripts/ledger_check.py`) is still green.

## Batch features

The full loop is in the dashboard. No CLI required.

### Run a batch — six clicks

1. **Load batch ▶** — fetches the queue + industry-mix bar. Glance at the mix; if it's thin, hit Scout fresh.
2. **Scout fresh ▼** *(optional)* — pick industries, Start. A chip in the header polls progress. On `done` the queue reloads.
3. **Label 20 roles** — for each: read the JD, click pursue / on-ramp / no, type a one-line reason. Score reveals.
4. **Done — review proposals ▶** — opens the propose modal. Each card shows: pattern, sample roles (your verdict vs the extraction), magnitude with old → new weight, and downstream re-band (how many previously-decided roles change band if accepted). Gate cards are flagged `low confidence` and need a manual edit if Accepted.
5. **Click Accept / Reject / Defer per card** — defaults to Defer until you click.
6. **Apply selections ▶** — server atomically edits the rubric for Accepted weight cards, runs `check.sh`, reverts on red, writes the audit. Counter advances unless reverted.

### Hard rules

- No rubric edit until Apply is clicked.
- Revert on red: any contradiction > 1 band against a logged human verdict triggers byte-for-byte rubric revert; counter does not advance.
- Gate accepts are recorded in the audit but NOT auto-applied — gate add/remove is a structural edit you make by hand.
- Defer queue: undecided proposals re-surface next batch with a "deferred from batch N" tag.
- Append-only: verdicts, ledger rows, and proposal events are appended; never rewritten.
