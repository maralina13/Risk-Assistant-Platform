# Runbook: local Kubernetes cluster

## Цель

Поднять локальный Kubernetes-кластер с Cilium CNI и подготовить namespaces для дальнейшего GitOps/deploy сценария.

## Предусловия

Нужно установить:

- Docker Desktop или совместимый container runtime;
- `minikube`;
- `kubectl`;
- `helm`.

## Команда

```bash
scripts/bootstrap_local_cluster.sh
```

Что делает скрипт:

1. Создает Minikube профиль `risk-assistant`.
2. Запускает 2-node кластер без стандартного CNI.
3. Ставит Cilium и Hubble.
4. Применяет базовые namespaces.

## Проверка

```bash
kubectl get nodes
kubectl -n kube-system get pods -l k8s-app=cilium
kubectl get ns risk-assistant kafka observability platform
```

