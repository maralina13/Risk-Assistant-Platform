# Platform implementation checklist

Этот документ покрывает вторую часть задания и связывает критерии с файлами проекта.

## Часть 1. Локальная инфраструктура и Kubernetes

### 1.1 Локальный Kubernetes + Cilium

Выбран вариант для локального стенда: Minikube или k3s/k0s. Для Cilium нужен кластер без стандартного CNI.

Команды для Minikube:

```bash
minikube start --driver=docker --network-plugin=cni --cni=false --nodes=2
helm repo add cilium https://helm.cilium.io/
helm upgrade --install cilium cilium/cilium \
  --namespace kube-system \
  --set kubeProxyReplacement=true \
  --set k8sServiceHost="$(minikube ip)" \
  --set k8sServicePort=8443 \
  --set hubble.enabled=true \
  --set hubble.relay.enabled=true \
  --set hubble.ui.enabled=true
```

Манифесты:
- `infra/kubernetes/cluster/cilium-network-policies.yaml`
- `infra/kubernetes/base/namespaces.yaml`

Runbook и bootstrap:
- `docs/runbooks/local-cluster.md`
- `scripts/bootstrap_local_cluster.sh`

### 1.2 Cluster Autoscaler

Для локального стенда выбран Cluster Autoscaler, потому что Karpenter полноценно раскрывается в облаке через cloud provider integration. В Minikube/Kubernetes lab он может быть установлен как демонстрация autoscaling control plane, а реальное добавление нод лучше проверять в k3s/k0s/Talos с поддерживаемым provisioner'ом или в managed cloud.

Манифест:
- `infra/kubernetes/cluster/cluster-autoscaler.yaml`

## Часть 2. IaC + GitOps

### 2.1 Terraform

Terraform описывает:
- namespaces;
- service accounts;
- базовые secrets;
- labels для Istio injection и observability.

Файл:
- `infra/terraform/main.tf`

### 2.2 ArgoCD App of Apps

Root application указывает на `infra/argocd/apps`, где лежат дочерние приложения:
- platform-infra;
- kafka;
- risk-assistant;
- observability.

Файлы:
- `infra/argocd/root-app.yaml`
- `infra/argocd/apps/*.yaml`

### 2.3 Ansible Role для Kafka

Ansible роль устанавливает Strimzi operator через Helm и применяет `Kafka` custom resource.

Файлы:
- `infra/ansible/roles/strimzi-kafka/tasks/main.yml`
- `infra/ansible/roles/strimzi-kafka/defaults/main.yml`
- `infra/ansible/roles/strimzi-kafka/templates/kafka-cluster.yaml.j2`
- `infra/ansible/deploy-kafka.yml`

## Часть 3. Ядро системы и трафик

### 3.1 Service Mesh

Выбран Istio, потому что он нативно использует Envoy, хорошо показывает retry, circuit breaker, outlier detection и интеграцию с Grafana/Kiali/Jaeger.

Файлы:
- `infra/kubernetes/mesh/istio-policies.yaml`
- `infra/helm/risk-assistant/templates/pdb.yaml`
- `infra/helm/risk-assistant/templates/networkpolicy.yaml`

### 3.2 Ingress + HAProxy + Keepalived

Для локального bare-metal-like стенда используется HAProxy Ingress Controller. Keepalived описан как VRRP слой для отказоустойчивого VIP перед ingress replicas.

Файлы:
- `infra/kubernetes/gateway/haproxy-ingress.yaml`
- `infra/kubernetes/gateway/keepalived.yaml`

### 3.3 Rate Limiting

Есть два уровня:
- application-level limiter в `services/api_gateway/main.py` через Valkey/Redis;
- gateway-level limiter в `infra/kubernetes/gateway/rate-limit.yaml` через Envoy/Istio local rate limit.

## Часть 4. Observability

Рассмотренные варианты:

| Слой | Варианты | Выбор |
| --- | --- | --- |
| Логи | Loki, VictoriaLogs, ELK, SigNoz | Loki для учебного стенда: проще и легче ELK |
| Метрики | Prometheus, VictoriaMetrics, InfluxDB | Prometheus для совместимости с Kubernetes ecosystem |
| Трейсы | Jaeger, Uptrace, Tempo | Tempo + OpenTelemetry Collector; Jaeger UI допустим как альтернатива |
| Визуализация | Grafana | Grafana |
| Alerting | Alertmanager, Grafana Alerting | Alertmanager |

Почему не ELK: тяжелее для локального стенда. Почему не VictoriaMetrics Cluster: хорош для production/high-cardinality, но в учебном Minikube избыточен. Почему не SigNoz: удобный all-in-one, но стек Prometheus/Loki/Tempo легче связать с Istio и Kafka dashboards.

Файлы:
- `infra/observability/kube-prometheus-values.yaml`
- `infra/observability/loki-values.yaml`
- `infra/observability/tempo-values.yaml`
- `infra/observability/otel-collector.yaml`
- `infra/observability/prometheus-rules.yaml`
- `infra/observability/dashboards/risk-assistant-dashboard.json`
- `infra/helm/risk-assistant/templates/servicemonitor.yaml`
- `infra/observability/servicemonitor-kafka.yaml`

Каждый Python-сервис отдает `/health` для readiness/liveness и `/metrics` в Prometheus text format для ServiceMonitor.

## Часть 5. CI/CD и окружение разработки

### 5.1 GitLab Runner

Для локального GitLab Runner:

```bash
helm repo add gitlab https://charts.gitlab.io
helm upgrade --install gitlab-runner gitlab/gitlab-runner \
  --namespace cicd --create-namespace \
  -f infra/ci/gitlab-runner-values.yaml
```

Для автономного локального демо без внешнего GitLab используется runner-скрипт:

```bash
IMAGE_TAG=ci-final-demo scripts/local_ci_pipeline.sh
```

Live-проверка: pipeline выполнил `pytest`, собрал Docker image, загрузил image в minikube,
обновил GitOps image tag, запушил изменение в локальный Git daemon и дождался ArgoCD rollout.

### 5.2 Pipeline

Pipeline:
1. Build image через Kaniko.
2. Push в local registry.
3. Update Helm Chart image tag.
4. ArgoCD Sync.

Файлы:
- `infra/ci/gitlab-ci.yml`
- `infra/ci/kaniko-build-job.yaml`
- `scripts/local_ci_pipeline.sh`

### 5.3 Helm charts для 3+ микросервисов

Chart разворачивает 6 сервисов:
- api-gateway;
- project-intake-service;
- risk-analysis-service;
- report-service;
- audit-service;
- notification-service.

Файлы:
- `infra/helm/risk-assistant/Chart.yaml`
- `infra/helm/risk-assistant/values.yaml`
- `infra/helm/risk-assistant/templates/*.yaml`

## Часть 6. Тестирование и валидация платформы

### 6.1 Locust

Файл:
- `tests/load/locustfile.py`

Пример запуска:

```bash
locust -f tests/load/locustfile.py --host http://localhost:8080
```

### 6.2 Circuit Breaker

Проверка:
1. Запустить Locust.
2. Во время теста искусственно сломать `report-service`, например масштабировать до 0:

```bash
kubectl -n risk-assistant scale deploy/report-service --replicas=0
```

3. Проверить в Istio metrics рост `istio_requests_total{response_code="503"}` и outlier/retry поведение.
4. Вернуть сервис:

```bash
kubectl -n risk-assistant scale deploy/report-service --replicas=2
```

Готовый скрипт:

```bash
scripts/demo_circuit_breaker.sh
```

### 6.3 Grafana dashboards

На dashboard должны быть видны:
- HTTP request rate и latency по gateway/service;
- Kafka consumer lag по topics;
- rate limiter hits / 429 responses;
- error rate и circuit breaker 5xx;
- CPU/memory сервисов;
- traces через Tempo.

Live validation:

```bash
scripts/validate_live_cluster.sh
```
