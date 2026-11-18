#!/usr/bin/env bash
#
# Smoke test for the expense tracker.
# Checks a running instance from the outside, for example after a deploy.
#
# Usage:
#   bash scripts/smoke-test.sh https://expense-tracker-xxxx.onrender.com
#
# Steps:
#   1. /health  (tried several times, because a sleeping free instance
#               needs up to a minute to wake up)
#   2. /ready
#   3. POST   /api/expenses        create a test expense
#   4. GET    /api/expenses        the new expense is in the list
#   5. DELETE /api/expenses/<id>   remove it again
#
# The script stops at the first failed check with exit code 1.
# Only when everything worked it prints "SMOKE TEST PASSED".
# Needs only bash, curl and grep.

set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <base-url>"
  exit 2
fi

# Remove a slash at the end, so we do not get "//health".
BASE_URL="${1%/}"

# How often /health is tried and how long to wait between tries.
# Can be changed from outside, e.g. HEALTH_RETRIES=20 bash scripts/smoke-test.sh ...
HEALTH_RETRIES="${HEALTH_RETRIES:-12}"
WAIT_SECONDS="${WAIT_SECONDS:-10}"

# curl writes the response body into this file, the status code goes to stdout.
BODY_FILE="$(mktemp)"
trap 'rm -f "$BODY_FILE"' EXIT

fail() {
  echo "FAIL: $1"
  exit 1
}

echo "Target: $BASE_URL"

# --- 1/5 /health -------------------------------------------------------------

echo "== 1/5 /health =="
attempt=1
healthy="no"
while [ "$attempt" -le "$HEALTH_RETRIES" ]; do
  # "|| true": if the instance is still asleep, curl fails. That is not an
  # error yet, we just try again.
  status="$(curl --silent --max-time 60 --output "$BODY_FILE" --write-out "%{http_code}" "$BASE_URL/health" || true)"
  if [ "$status" = "200" ] && grep -q '"status":"ok"' "$BODY_FILE"; then
    echo "  OK (attempt $attempt): $(cat "$BODY_FILE")"
    healthy="yes"
    break
  fi
  echo "  not ready yet (attempt $attempt of $HEALTH_RETRIES), waiting $WAIT_SECONDS s"
  sleep "$WAIT_SECONDS"
  attempt=$((attempt + 1))
done

if [ "$healthy" != "yes" ]; then
  fail "/health did not answer with 200 after $HEALTH_RETRIES attempts"
fi

# --- 2/5 /ready --------------------------------------------------------------

echo "== 2/5 /ready =="
status="$(curl --silent --max-time 30 --output "$BODY_FILE" --write-out "%{http_code}" "$BASE_URL/ready")"
if [ "$status" != "200" ]; then
  fail "/ready returned $status, expected 200"
fi
echo "  OK: $(cat "$BODY_FILE")"

# --- 3/5 create an expense ---------------------------------------------------

echo "== 3/5 POST /api/expenses =="
status="$(curl --silent --max-time 30 --output "$BODY_FILE" --write-out "%{http_code}" \
  --header "Content-Type: application/json" \
  --data '{"amount_cents": 123, "category": "smoketest", "spent_on": "2026-01-01"}' \
  "$BASE_URL/api/expenses")"
if [ "$status" != "201" ]; then
  fail "POST returned $status, expected 201. Body: $(cat "$BODY_FILE")"
fi

# Take the number after "id": out of the answer, e.g. {"id":7,...} -> 7
expense_id="$(grep -oE '"id": ?[0-9]+' "$BODY_FILE" | grep -oE '[0-9]+')"
if [ -z "$expense_id" ]; then
  fail "no id in the answer: $(cat "$BODY_FILE")"
fi
echo "  created expense with id $expense_id"

# --- 4/5 the expense is in the list ------------------------------------------

echo "== 4/5 GET /api/expenses =="
status="$(curl --silent --max-time 30 --output "$BODY_FILE" --write-out "%{http_code}" "$BASE_URL/api/expenses?category=smoketest")"
if [ "$status" != "200" ]; then
  fail "GET returned $status, expected 200"
fi
if ! grep -qE "\"id\": ?$expense_id[,}]" "$BODY_FILE"; then
  fail "expense $expense_id is not in the list: $(cat "$BODY_FILE")"
fi
echo "  expense $expense_id found in the list"

# --- 5/5 delete it again -----------------------------------------------------

echo "== 5/5 DELETE /api/expenses/$expense_id =="
status="$(curl --silent --max-time 30 --output /dev/null --write-out "%{http_code}" \
  --request DELETE "$BASE_URL/api/expenses/$expense_id")"
if [ "$status" != "204" ]; then
  fail "DELETE returned $status, expected 204"
fi
echo "  deleted expense $expense_id"

echo
echo "SMOKE TEST PASSED"
