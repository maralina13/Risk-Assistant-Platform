#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-risk-assistant}"
HOST="${HOST:-http://localhost:8080}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$PROJECT_ROOT/.tools/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"
export MINIKUBE_HOME="${MINIKUBE_HOME:-$PROJECT_ROOT/.tools/minikube-home}"

require() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command is missing: $1" >&2
    exit 1
  fi
}

require kubectl
require curl

kubectl get namespace "$NAMESPACE" >/dev/null
kubectl get deploy -n "$NAMESPACE" api-gateway project-intake-service risk-analysis-service report-service audit-service notification-service >/dev/null
kubectl get svc -n "$NAMESPACE" api-gateway project-intake-service risk-analysis-service report-service audit-service notification-service >/dev/null

echo "Kubernetes objects are present"

if curl -fsS "$HOST/routes" >/dev/null; then
  echo "Gateway route check passed: $HOST/routes"
else
  echo "Gateway route check skipped or failed. If running in Kubernetes, port-forward first:" >&2
  echo "kubectl -n $NAMESPACE port-forward svc/api-gateway 8080:8088" >&2
  exit 1
fi
