#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

export PATH="$PROJECT_ROOT/.tools/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"
export MINIKUBE_HOME="${MINIKUBE_HOME:-$PROJECT_ROOT/.tools/minikube-home}"
CONTEXT="${CONTEXT:-risk-assistant}"
HOST_HEADER="${HOST_HEADER:-risk-assistant.local}"
LOCAL_PORT="${LOCAL_PORT:-18080}"
PORT_FORWARD_PID=""

cleanup() {
  if [[ -n "$PORT_FORWARD_PID" ]]; then
    kill "$PORT_FORWARD_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

kubectl --context "$CONTEXT" -n ingress-system port-forward svc/haproxy-ingress-kubernetes-ingress "$LOCAL_PORT":80 >/tmp/risk-assistant-haproxy-port-forward.log 2>&1 &
PORT_FORWARD_PID="$!"
sleep 3

HOST="http://localhost:$LOCAL_PORT"
echo "Checking API through HAProxy Ingress: $HOST/routes Host: $HOST_HEADER"
curl -fsS -H "Host: $HOST_HEADER" "$HOST/routes"

echo
echo "Submitting E2E request through HAProxy Ingress"
response="$(curl -fsS -H "Host: $HOST_HEADER" -X POST "$HOST/projects/analyze" \
  -H 'Content-Type: application/json' \
  -d '{"project_title":"Ingress E2E Allergy App","project_description":"Команда из двух человек хочет сделать мобильное приложение с картой кафе для людей с аллергией, без глютена и без лактозы. Начать планируют с Турции и потом расширяться на другие страны. Есть полгода, важна модерация данных и надежность рекомендаций."}')"
echo "$response"
task_id="$(printf '%s' "$response" | python3 -c 'import json,sys; print(json.load(sys.stdin)["task_id"])')"

for attempt in $(seq 1 20); do
  status_code="$(curl -sS -H "Host: $HOST_HEADER" -o /tmp/risk-assistant-ingress-report.json -w '%{http_code}' "$HOST/reports/$task_id")"
  if [[ "$status_code" == "200" ]]; then
    python3 -c 'import json,sys; print(json.dumps(json.load(open(sys.argv[1], encoding="utf-8")), ensure_ascii=False, indent=2))' /tmp/risk-assistant-ingress-report.json
    echo "Ingress E2E passed: task_id=$task_id"
    exit 0
  fi
  echo "Attempt $attempt: report is not ready yet, HTTP $status_code"
  sleep 2
done

echo "Ingress E2E failed: report was not ready" >&2
exit 1
