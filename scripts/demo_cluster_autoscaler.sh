#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

export PATH="$PROJECT_ROOT/.tools/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"
export MINIKUBE_HOME="${MINIKUBE_HOME:-$PROJECT_ROOT/.tools/minikube-home}"
CONTEXT="${CONTEXT:-risk-assistant}"

cleanup() {
  if [[ "${KEEP_AUTOSCALER_DEMO:-0}" != "1" ]]; then
    kubectl --context "$CONTEXT" -n platform delete deployment autoscaler-probe --ignore-not-found=true >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "==> apply unschedulable workload for Cluster Autoscaler demo"
kubectl --context "$CONTEXT" apply -f infra/kubernetes/cluster/autoscaler-demo-workload.yaml

echo "==> wait until scheduler marks pods pending"
kubectl --context "$CONTEXT" -n platform wait --for=jsonpath='{.status.phase}'=Pending pod -l app.kubernetes.io/name=autoscaler-probe --timeout=90s

echo "==> current autoscaler probe pods"
kubectl --context "$CONTEXT" -n platform get pods -l app.kubernetes.io/name=autoscaler-probe -o wide

echo "==> give Cluster Autoscaler one reconciliation loop to observe pending pods"
sleep "${AUTOSCALER_DEMO_WAIT_SECONDS:-35}"

echo "==> Cluster Autoscaler recent log lines"
kubectl --context "$CONTEXT" -n kube-system logs deploy/cluster-autoscaler --since=2m | \
  grep -E 'unschedulable|Upcoming|Scale-up|Best option|No expansion|kwok|pod' || true

echo "Cluster Autoscaler demo finished. Set KEEP_AUTOSCALER_DEMO=1 to leave the probe workload in place."
