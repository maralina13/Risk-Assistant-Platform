#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTEXT="${CONTEXT:-risk-assistant}"
APP_NAMESPACE="${APP_NAMESPACE:-risk-assistant}"
ARGO_NAMESPACE="${ARGO_NAMESPACE:-argocd}"
OBS_NAMESPACE="${OBS_NAMESPACE:-observability}"
KAFKA_NAMESPACE="${KAFKA_NAMESPACE:-kafka}"

export PATH="$PROJECT_ROOT/.tools/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"
export MINIKUBE_HOME="${MINIKUBE_HOME:-$PROJECT_ROOT/.tools/minikube-home}"

require() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command is missing: $1" >&2
    exit 1
  fi
}

section() {
  printf '\n== %s ==\n' "$1"
}

require kubectl

section "Kubernetes nodes"
kubectl --context "$CONTEXT" get nodes

section "ArgoCD applications"
kubectl --context "$CONTEXT" -n "$ARGO_NAMESPACE" get applications.argoproj.io

section "Microservices"
kubectl --context "$CONTEXT" -n "$APP_NAMESPACE" get deploy \
  api-gateway \
  project-intake-service \
  risk-analysis-service \
  report-service \
  audit-service \
  notification-service \
  -o 'custom-columns=NAME:.metadata.name,READY:.status.readyReplicas,AVAILABLE:.status.availableReplicas,IMAGE:.spec.template.spec.containers[0].image'

section "Kafka and platform pods"
kubectl --context "$CONTEXT" -n "$KAFKA_NAMESPACE" get pod risk-kafka-0
kubectl --context "$CONTEXT" -n istio-system get pods
kubectl --context "$CONTEXT" -n kube-system get pods -l k8s-app=cilium

section "Observability resources"
kubectl --context "$CONTEXT" -n "$APP_NAMESPACE" get servicemonitor
kubectl --context "$CONTEXT" -n "$OBS_NAMESPACE" get prometheusrule risk-assistant-alerts
kubectl --context "$CONTEXT" -n "$OBS_NAMESPACE" get configmap risk-assistant-grafana-dashboard

section "Repository self-check"
python3 "$PROJECT_ROOT/scripts/check_submission.py"

section "Done"
echo "Smoke check finished. For API E2E, port-forward svc/api-gateway 8080:8088 and run the curl command from docs/submission-handoff.md."
