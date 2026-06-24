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

- **Diverse scouting**: the queue picks at most 4 roles per industry per batch of 20. Industry is read from jd.md `domain: <industry>:<archetype>` (seeded by reference/domain-map.md). Untagged roles bucket as "unknown".
- **Batch summary**: in the dashboard, click "Show batch summary ▾" to see verdict mix, per-industry hit rates, machine-fit spread by verdict bucket, divergences, and proposed weight deltas. The CLI equivalent is `python3 review.py --batch-summary`.
- **End-of-batch loop**:
  1. `bash skills/calibrate/scripts/run.sh` — opens dashboard, label 20 roles (industry-diverse).
  2. Click "Show batch summary ▾" → review the picture.
  3. `python3 skills/calibrate/scripts/review.py` — appends status:proposed deltas to reference/lessons.md.
  4. Edit fit-rubric.md to ratify deltas.
  5. `bash skills/score-fit/scripts/check.sh` — must stay green.
  6. Next batch.
