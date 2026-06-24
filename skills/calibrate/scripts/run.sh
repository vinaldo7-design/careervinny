#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
echo "==> running guards before serving"
bash ../../score-fit/scripts/check.sh
python3 test_log.py
python3 test_queue.py
python3 test_server.py
python3 test_review.py
echo
N=$(wc -l < ../../../calibration-log.jsonl | tr -d ' ')
echo "==> calibration log has $N verdicts"
if [ "$N" -ge 20 ]; then
  echo "    >=20 verdicts — consider: python3 review.py"
fi
echo "==> starting dashboard on http://127.0.0.1:8765"
exec python3 server.py
