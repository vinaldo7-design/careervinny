#!/usr/bin/env bash
# Run after EVERY score-fit engine or rubric change. A red here = a regression.
#   - test_scorer.py       : engine math + gates + evidence gate (fixtures)
#   - test_ledger_check.py : the regression-guard logic itself
#   - ledger_check.py      : the live guard — machine vs every decided role in the ledger
set -e
cd "$(dirname "$0")"
python3 test_scorer.py
echo
python3 test_ledger_check.py
echo
python3 ledger_check.py
