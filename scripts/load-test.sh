#!/usr/bin/env bash
# Generate HTTP load against the Expense Tracker, so Prometheus has something
# to measure. Mostly normal requests plus a few deliberate client errors
# (400, 404), so the status panel shows more than just 2xx.
#
# Usage:
#   scripts/load-test.sh                              # 200 rounds against localhost:8000
#   scripts/load-test.sh http://localhost:8000 500    # URL and number of rounds
#
# Stop early with Ctrl+C.
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
ROUNDS="${2:-200}"

echo "Generating load against ${BASE_URL} for ${ROUNDS} rounds..."

for i in $(seq 1 "${ROUNDS}"); do
  # Normal traffic: create an expense, list, filter, summary, liveness.
  curl -s -o /dev/null -X POST -H "Content-Type: application/json" \
    -d '{"amount_cents": 1250, "category": "food", "spent_on": "2026-11-24"}' \
    "${BASE_URL}/api/expenses"
  curl -s -o /dev/null "${BASE_URL}/api/expenses"
  curl -s -o /dev/null "${BASE_URL}/api/expenses?category=food&month=2026-11"
  curl -s -o /dev/null "${BASE_URL}/api/expenses/summary"
  curl -s -o /dev/null "${BASE_URL}/health"

  # Every 5th round: invalid input -> 400 (client error).
  if (( i % 5 == 0 )); then
    curl -s -o /dev/null -X POST -H "Content-Type: application/json" \
      -d '{"amount_cents": -1, "category": "food", "spent_on": "2026-11-24"}' \
      "${BASE_URL}/api/expenses"
  fi

  # Every 10th round: unknown route -> 404 (client error).
  if (( i % 10 == 0 )); then
    curl -s -o /dev/null "${BASE_URL}/does-not-exist"
  fi

  # Small pause, so the load is spread over time instead of one burst.
  sleep 0.1
done

echo "Done. Wait 15-30 s (one or two scrapes) before looking at the dashboard."
