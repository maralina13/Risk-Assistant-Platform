#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTEXT="${CONTEXT:-risk-assistant}"
NAMESPACE="${NAMESPACE:-risk-assistant}"
HOST="${HOST:-http://localhost:8080}"
START_PORT_FORWARD="${START_PORT_FORWARD:-0}"
PORT_FORWARD_PID=""

export PATH="$PROJECT_ROOT/.tools/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"
export MINIKUBE_HOME="${MINIKUBE_HOME:-$PROJECT_ROOT/.tools/minikube-home}"

cleanup() {
  if [[ -n "$PORT_FORWARD_PID" ]]; then
    kill "$PORT_FORWARD_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

require() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command is missing: $1" >&2
    exit 1
  fi
}

json_field() {
  python3 -c 'import json,sys; print(json.load(sys.stdin).get(sys.argv[1], ""))' "$1"
}

json_pretty() {
  python3 -c 'import json,sys; print(json.dumps(json.load(open(sys.argv[1], encoding="utf-8")), ensure_ascii=False, indent=2))' "$1"
}

require curl
require python3

if [[ "$START_PORT_FORWARD" == "1" ]]; then
  require kubectl
  kubectl --context "$CONTEXT" -n "$NAMESPACE" port-forward svc/api-gateway 8080:8088 >/tmp/risk-assistant-api-gateway-port-forward.log 2>&1 &
  PORT_FORWARD_PID="$!"
  sleep 3
fi

echo "Checking API Gateway routes at $HOST/routes"
curl -fsS "$HOST/routes" >/tmp/risk-assistant-routes.json
json_pretty /tmp/risk-assistant-routes.json

echo
echo "Submitting project analysis request"
cat >/tmp/risk-assistant-project.json <<'JSON'
{
  "project_title": "Defense E2E Allergy App",
  "project_description": "Команда из двух человек хочет сделать мобильное приложение с картой кафе для людей с аллергией, без глютена и без лактозы. Начать планируют с Турции и потом расширяться на другие страны. Есть полгода, важна модерация данных и надежность рекомендаций."
}
JSON

curl -fsS -X POST "$HOST/projects/analyze" \
  -H 'Content-Type: application/json' \
  --data-binary @/tmp/risk-assistant-project.json \
  >/tmp/risk-assistant-submit.json

json_pretty /tmp/risk-assistant-submit.json
TASK_ID="$(json_field task_id </tmp/risk-assistant-submit.json)"

if [[ -z "$TASK_ID" ]]; then
  echo "Response does not contain task_id" >&2
  exit 1
fi

echo
echo "Waiting for report: $TASK_ID"
for attempt in $(seq 1 20); do
  status_code="$(curl -sS -o /tmp/risk-assistant-report.json -w '%{http_code}' "$HOST/reports/$TASK_ID")"
  if [[ "$status_code" == "200" ]]; then
    json_pretty /tmp/risk-assistant-report.json
    echo
    echo "E2E demo passed: task_id=$TASK_ID"
    exit 0
  fi
  echo "Attempt $attempt: report is not ready yet, HTTP $status_code"
  sleep 2
done

echo "Report was not ready after polling. Last response:" >&2
cat /tmp/risk-assistant-report.json >&2
exit 1
