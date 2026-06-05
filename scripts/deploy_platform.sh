#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-risk-assistant}"
IMAGE_REPOSITORY="${IMAGE_REPOSITORY:-localhost:5000/risk-assistant}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
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
require helm

kubectl apply -f infra/kubernetes/base/namespaces.yaml
kubectl apply -f infra/kubernetes/mesh/istio-policies.yaml || true
kubectl apply -f infra/kubernetes/gateway/haproxy-ingress.yaml || true
kubectl apply -f infra/kubernetes/gateway/rate-limit.yaml || true

helm upgrade --install risk-assistant infra/helm/risk-assistant \
  --namespace "$NAMESPACE" \
  --create-namespace \
  --set "image.repository=$IMAGE_REPOSITORY" \
  --set "image.tag=$IMAGE_TAG"

kubectl rollout status -n "$NAMESPACE" deploy/api-gateway --timeout=5m
kubectl rollout status -n "$NAMESPACE" deploy/project-intake-service --timeout=5m
kubectl rollout status -n "$NAMESPACE" deploy/risk-analysis-service --timeout=5m
kubectl rollout status -n "$NAMESPACE" deploy/report-service --timeout=5m

echo "Risk Assistant platform deployed to namespace: $NAMESPACE"
