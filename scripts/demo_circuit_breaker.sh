#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-risk-assistant}"
TARGET_DEPLOYMENT="${TARGET_DEPLOYMENT:-report-service}"
DOWN_SECONDS="${DOWN_SECONDS:-30}"
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

echo "Scaling $TARGET_DEPLOYMENT to 0 replicas to trigger retry/outlier behavior"
kubectl -n "$NAMESPACE" scale "deploy/$TARGET_DEPLOYMENT" --replicas=0
sleep "$DOWN_SECONDS"

echo "Restoring $TARGET_DEPLOYMENT to 2 replicas"
kubectl -n "$NAMESPACE" scale "deploy/$TARGET_DEPLOYMENT" --replicas=2
kubectl -n "$NAMESPACE" rollout status "deploy/$TARGET_DEPLOYMENT" --timeout=5m

echo "Circuit breaker demo finished. Check Grafana for 5xx/503, latency and recovery."
