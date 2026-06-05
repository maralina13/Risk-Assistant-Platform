#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

export PATH="$PROJECT_ROOT/.tools/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"
export MINIKUBE_HOME="${MINIKUBE_HOME:-$PROJECT_ROOT/.tools/minikube-home}"
CONTEXT="${CONTEXT:-risk-assistant}"
CONTEXT_ARCHIVE_DIR="${CONTEXT_ARCHIVE_DIR:-/tmp/risk-assistant-kaniko-context}"
CONTEXT_PORT="${CONTEXT_PORT:-18081}"

cleanup_context_server() {
  if [[ -n "${CONTEXT_SERVER_PID:-}" ]]; then
    kill "$CONTEXT_SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup_context_server EXIT

echo "==> prepare Kaniko build context archive"
rm -rf "$CONTEXT_ARCHIVE_DIR"
mkdir -p "$CONTEXT_ARCHIVE_DIR"
tar \
  --exclude './.git' \
  --exclude './.tools' \
  --exclude './.venv' \
  --exclude './outputs' \
  --exclude './runtime' \
  --exclude './logs' \
  --exclude './reports' \
  --exclude './artifacts' \
  -czf "$CONTEXT_ARCHIVE_DIR/context.tar.gz" \
  -C "$PROJECT_ROOT" \
  .
python3 -m http.server "$CONTEXT_PORT" --bind 0.0.0.0 --directory "$CONTEXT_ARCHIVE_DIR" >/tmp/risk-assistant-kaniko-context-http.log 2>&1 &
CONTEXT_SERVER_PID="$!"
sleep 1

echo "==> ensure cicd namespace and registry"
kubectl --context "$CONTEXT" apply -f infra/kubernetes/base/namespaces.yaml
kubectl --context "$CONTEXT" apply -f infra/kubernetes/ci/local-registry.yaml
kubectl --context "$CONTEXT" -n cicd rollout status deploy/cicd-registry --timeout=180s

echo "==> run Kaniko build job inside Kubernetes"
kubectl --context "$CONTEXT" -n cicd delete job risk-assistant-kaniko-live --ignore-not-found=true
kubectl --context "$CONTEXT" apply -f infra/ci/kaniko-live-job.yaml
kubectl --context "$CONTEXT" -n cicd wait --for=condition=complete job/risk-assistant-kaniko-live --timeout=600s

echo "==> verify image pushed to in-cluster registry"
kubectl --context "$CONTEXT" -n cicd run registry-check \
  --image=curlimages/curl:8.10.1 \
  --restart=Never \
  --rm \
  -i \
  --quiet \
  --command -- curl -fsS http://cicd-registry.cicd.svc.cluster.local:5000/v2/risk-assistant/tags/list

echo "Live Kaniko pipeline finished: cicd-registry.cicd.svc.cluster.local:5000/risk-assistant:ci-kaniko-live"
