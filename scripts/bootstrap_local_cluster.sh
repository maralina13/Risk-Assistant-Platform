#!/usr/bin/env bash
set -euo pipefail

CLUSTER_DRIVER="${CLUSTER_DRIVER:-docker}"
MINIKUBE_PROFILE="${MINIKUBE_PROFILE:-risk-assistant}"
MINIKUBE_NODES="${MINIKUBE_NODES:-2}"
MINIKUBE_CPUS="${MINIKUBE_CPUS:-2}"
MINIKUBE_MEMORY="${MINIKUBE_MEMORY:-3072}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$PROJECT_ROOT/.tools/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"
export MINIKUBE_HOME="${MINIKUBE_HOME:-$PROJECT_ROOT/.tools/minikube-home}"

require() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command is missing: $1" >&2
    exit 1
  fi
}

require minikube
require kubectl
require helm

minikube start \
  --profile "$MINIKUBE_PROFILE" \
  --driver "$CLUSTER_DRIVER" \
  --network-plugin=cni \
  --cni=false \
  --nodes="$MINIKUBE_NODES" \
  --cpus="$MINIKUBE_CPUS" \
  --memory="$MINIKUBE_MEMORY"

helm repo add cilium https://helm.cilium.io/ >/dev/null
helm repo update >/dev/null

helm upgrade --install cilium cilium/cilium \
  --namespace kube-system \
  --set kubeProxyReplacement=true \
  --set "k8sServiceHost=$(minikube -p "$MINIKUBE_PROFILE" ip)" \
  --set k8sServicePort=8443 \
  --set hubble.enabled=true \
  --set hubble.relay.enabled=true \
  --set hubble.ui.enabled=true

kubectl rollout status -n kube-system ds/cilium --timeout=5m
kubectl apply -f infra/kubernetes/base/namespaces.yaml

echo "Local cluster is ready: $MINIKUBE_PROFILE"
