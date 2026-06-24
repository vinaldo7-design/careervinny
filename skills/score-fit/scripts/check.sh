#!/usr/bin/env bash
# Run after EVERY score-fit engine or rubric change. A red here = a regression.
#   - test_scorer.py        : engine math + gates + evidence gate (fixtures)
#   - test_ledger_check.py  : the regression-guard logic itself
#   - ledger_check.py       : the live guard — machine vs every decided role in the ledger
#   - calibrate tests       : queue, log, review pure-fn tests (no server boot)
set -e
cd "$(dirname "$0")"
python3 test_scorer.py
echo
python3 test_ledger_check.py
echo
python3 ledger_check.py
echo
echo "==> calibrate pure-fn tests"
( cd ../../calibrate/scripts && python3 test_log.py && python3 test_queue.py && python3 test_review.py )
echo
echo "==> calibrate batch-loop tests"
( cd ../../calibrate/scripts && python3 test_batch_state.py && python3 test_proposals.py && python3 test_defer_queue.py && python3 test_apply_proposals.py && python3 test_scout_runner.py && python3 test_e2e_batch.py )
