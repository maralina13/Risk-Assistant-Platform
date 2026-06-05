#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

export PATH="$PROJECT_ROOT/.tools/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"
export MINIKUBE_HOME="${MINIKUBE_HOME:-$PROJECT_ROOT/.tools/minikube-home}"

IMAGE_REPOSITORY="${IMAGE_REPOSITORY:-localhost:5000/risk-assistant}"
IMAGE_TAG="${IMAGE_TAG:-ci-local-$(date +%Y%m%d%H%M%S)}"
NAMESPACE="${NAMESPACE:-risk-assistant}"
GITOPS_APP_FILE="${GITOPS_APP_FILE:-infra/argocd/apps/risk-assistant.yaml}"
GITOPS_WORKTREE="${GITOPS_WORKTREE:-$(ls -td /tmp/risk-assistant-git-src.* 2>/dev/null | head -1 || true)}"
GITOPS_BARE_REPO="${GITOPS_BARE_REPO:-$(ls -td /tmp/risk-assistant-git-base.*/risk-assistant.git 2>/dev/null | head -1 || true)}"

echo "==> test"
if [[ -x .venv/bin/python ]]; then
  .venv/bin/python -m pytest -q
else
  python3 -m pytest -q
fi

echo "==> build image: ${IMAGE_REPOSITORY}:${IMAGE_TAG}"
docker build -t "${IMAGE_REPOSITORY}:${IMAGE_TAG}" .

echo "==> load image into minikube profile risk-assistant"
minikube -p risk-assistant image load "${IMAGE_REPOSITORY}:${IMAGE_TAG}"

echo "==> update GitOps Helm parameters"
python3 - "$GITOPS_APP_FILE" "$IMAGE_REPOSITORY" "$IMAGE_TAG" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
repository = sys.argv[2]
tag = sys.argv[3]
lines = path.read_text(encoding="utf-8").splitlines()
current_name = None
for index, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith("- name: "):
        current_name = stripped.removeprefix("- name: ").strip()
        continue
    if stripped.startswith("value: ") and current_name == "image.repository":
        indent = line[: len(line) - len(line.lstrip())]
        lines[index] = f"{indent}value: {repository}"
        current_name = None
    elif stripped.startswith("value: ") and current_name == "image.tag":
        indent = line[: len(line) - len(line.lstrip())]
        lines[index] = f"{indent}value: {tag}"
        current_name = None
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

if [[ -n "$GITOPS_WORKTREE" && -n "$GITOPS_BARE_REPO" ]]; then
  echo "==> push GitOps update to local git daemon source"
  rsync -a --delete --exclude '.tools' --exclude '.git' ./ "$GITOPS_WORKTREE/"
  git -C "$GITOPS_WORKTREE" add .
  git -C "$GITOPS_WORKTREE" commit -m "ci: deploy ${IMAGE_TAG}" || true
  git -C "$GITOPS_WORKTREE" push "$GITOPS_BARE_REPO" main
else
  echo "No local GitOps worktree detected; keeping update in working tree only."
fi

echo "==> sync through ArgoCD if installed, otherwise fallback to helm upgrade"
if kubectl -n argocd get application risk-assistant >/dev/null 2>&1; then
  kubectl -n argocd annotate application risk-assistant-root argocd.argoproj.io/refresh=hard --overwrite || true
  kubectl -n argocd annotate application risk-assistant argocd.argoproj.io/refresh=hard --overwrite
  for _ in $(seq 1 60); do
    deployed_image="$(kubectl -n "$NAMESPACE" get deploy/api-gateway -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || true)"
    if [[ "$deployed_image" == "${IMAGE_REPOSITORY}:${IMAGE_TAG}" ]]; then
      break
    fi
    sleep 5
  done
else
  helm upgrade risk-assistant infra/helm/risk-assistant \
    -n "$NAMESPACE" \
    --set image.repository="$IMAGE_REPOSITORY" \
    --set image.tag="$IMAGE_TAG" \
    --set serviceMonitor.enabled=false \
    --set networkPolicy.enabled=false \
    --wait \
    --timeout 5m
fi

echo "==> validate"
kubectl -n "$NAMESPACE" rollout status deploy/api-gateway --timeout=5m
kubectl -n "$NAMESPACE" rollout status deploy/project-intake-service --timeout=5m
kubectl -n "$NAMESPACE" rollout status deploy/risk-analysis-service --timeout=5m
kubectl -n "$NAMESPACE" rollout status deploy/report-service --timeout=5m
deployed_image="$(kubectl -n "$NAMESPACE" get deploy/api-gateway -o jsonpath='{.spec.template.spec.containers[0].image}')"
echo "$deployed_image"
if [[ "$deployed_image" != "${IMAGE_REPOSITORY}:${IMAGE_TAG}" ]]; then
  echo "Expected deployed image ${IMAGE_REPOSITORY}:${IMAGE_TAG}, got ${deployed_image}" >&2
  exit 1
fi

echo "Local CI pipeline finished: ${IMAGE_REPOSITORY}:${IMAGE_TAG}"
