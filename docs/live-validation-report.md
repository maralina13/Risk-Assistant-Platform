# Live validation report

Дата проверки: 2026-05-28.

Этот файл фиксирует фактическое состояние локального Kubernetes-стенда после развертывания,
GitOps-синхронизации, CI/CD-прогона, observability-проверки, Locust-нагрузки и circuit breaker demo.

## 1. Kubernetes cluster

Команда:

```bash
kubectl get nodes
```

Фактический результат:

```text
risk-assistant       Ready   control-plane   v1.35.1
risk-assistant-m02   Ready   worker          v1.35.1
```

Вывод: локальный кластер поднят, состоит из control-plane и worker node.

## 2. Platform components

Проверенные компоненты:

- Cilium CNI: pods `cilium-*` и `cilium-operator-*` Running.
- Cluster Autoscaler: `cluster-autoscaler` Running в `kube-system`, KWOK provider config загружен.
- Istio: `istiod` Running.
- HAProxy Ingress Controller: `haproxy-ingress-kubernetes-ingress` Running.
- Keepalived: DaemonSet Running на control-plane и worker node.
- Kafka/Redpanda: `risk-kafka-0` Running.
- Prometheus/Grafana/Alertmanager: все pods Running.
- OpenTelemetry Collector: `otel-collector` Running.
- ArgoCD: `argocd-server`, `argocd-repo-server`, `argocd-application-controller` Running.

Cluster Autoscaler demo-нагрузка:

```bash
scripts/demo_cluster_autoscaler.sh
```

Сценарий создает `autoscaler-probe` deployment с CPU request `3500m`, чтобы получить pending pods
и показать, что Cluster Autoscaler анализирует scheduling pressure. Фактический результат:

```text
autoscaler-probe pods: Pending
Cluster Autoscaler: 4 unschedulable pods left
Pod platform/autoscaler-probe-... is unschedulable
No expansion options
```

Вывод: autoscaler-контроллер работает и видит нагрузку, но в Docker-based Minikube без реального
cloud/Cluster API provider он не создает настоящие worker nodes. По умолчанию demo workload
удаляется после проверки.

## 3. ArgoCD App of Apps

Команда:

```bash
kubectl -n argocd get applications.argoproj.io
```

Фактический результат:

```text
kafka                 Synced   Healthy
observability         Synced   Healthy
platform-infra        Synced   Healthy
risk-assistant        Synced   Healthy
risk-assistant-root   Synced   Healthy
```

Вывод: App of Apps работает, дочерние приложения синхронизированы из GitOps source.

## 4. Microservices

Команда:

```bash
kubectl -n risk-assistant get deploy api-gateway project-intake-service \
  risk-analysis-service report-service audit-service notification-service \
  -o 'custom-columns=NAME:.metadata.name,READY:.status.readyReplicas,IMAGE:.spec.template.spec.containers[0].image'
```

Фактический результат:

```text
api-gateway              2   localhost:5000/risk-assistant:ci-final-demo
project-intake-service   2   localhost:5000/risk-assistant:ci-final-demo
risk-analysis-service    2   localhost:5000/risk-assistant:ci-final-demo
report-service           2   localhost:5000/risk-assistant:ci-final-demo
audit-service            1   localhost:5000/risk-assistant:ci-final-demo
notification-service     1   localhost:5000/risk-assistant:ci-final-demo
```

Вывод: все 6 микросервисов развернуты через Helm/ArgoCD и используют image,
полученный после локального CI/CD-прогона.

## 5. CI/CD validation

Live Kubernetes Kaniko build:

```bash
scripts/live_kaniko_pipeline.sh
```

Фактический результат:

```text
job.batch/risk-assistant-kaniko-live condition met
{"name":"risk-assistant","tags":["latest","ci-kaniko-live"]}
Live Kaniko pipeline finished: cicd-registry.cicd.svc.cluster.local:5000/risk-assistant:ci-kaniko-live
```

Вывод: Kaniko job выполняется внутри Kubernetes, получает tar.gz build context через initContainer,
собирает image и push'ит его в registry `cicd-registry` внутри namespace `cicd`.

Local GitOps pipeline:

Команда:

```bash
IMAGE_TAG=ci-final-demo scripts/local_ci_pipeline.sh
```

Фактический результат:

```text
10 passed
Docker image built: localhost:5000/risk-assistant:ci-final-demo
image loaded into minikube
GitOps source updated
ArgoCD synced
rollouts validated
Local CI pipeline finished: localhost:5000/risk-assistant:ci-final-demo
```

Вывод: pipeline покрывает test, build, image publishing/loading, GitOps update, ArgoCD sync и rollout validation.

## 6. Observability validation

Проверенные ресурсы:

```text
ServiceMonitor: api-gateway, audit-service, notification-service,
project-intake-service, report-service, risk-analysis-service

PrometheusRule: risk-assistant-alerts
Grafana dashboard ConfigMap: risk-assistant-grafana-dashboard
```

Prometheus scrape проверен через API:

```text
risk-assistant targets: 10
healthy targets: 10
sum(risk_assistant_service_up): 10
```

Вывод: Prometheus видит и успешно scrape'ит все pod targets микросервисов.

Deep logs/traces validation:

```bash
scripts/validate_observability_deep.sh
```

Фактический результат:

```text
Loki readiness: ready
Loki query: result contains defense observability log
Tempo readiness: ready
OTel Collector /v1/traces: {"partialSuccess":{}}
Tempo query: trace returned by /api/traces/{trace_id}
OTel logs: TracesExporter resource spans 1, spans 1
```

Вывод: логи и трейсы не только описаны в manifests. Loki принимает и отдаёт тестовую запись,
а OpenTelemetry Collector принимает OTLP trace и прокидывает его в Tempo.

## 7. Load test

Команда:

```bash
locust -f tests/load/locustfile.py --host http://localhost:8080 \
  --headless --users 25 --spawn-rate 5 --run-time 45s --only-summary
```

Фактический результат:

```text
859 requests
0 failures
~19 req/s
median latency ~9 ms
```

Отдельный более жесткий прогон подтвердил работу rate limiter: `POST /projects/analyze`
получал `429 Too Many Requests`.

## 8. Circuit breaker / failure demo

Сценарий:

```bash
locust -f tests/load/locustfile.py --host http://localhost:8080 \
  --headless --users 15 --spawn-rate 5 --run-time 70s --only-summary
DOWN_SECONDS=20 scripts/demo_circuit_breaker.sh
```

Фактический результат:

```text
report-service scaled to 0
GET /reports/{missing}: temporary failures during outage
report-service restored to 2/2
rollout successfully finished
```

Вывод: отказ сервиса и восстановление были проверены на live-трафике.

## 9. Submission self-check

Команда:

```bash
python3 scripts/check_submission.py
```

Фактический результат:

```text
Required files present: 61
JSON files are valid: 9
Python files compile: 23
Documentation contains required architecture terms
Microservice directories found: 6
Executable shell scripts with valid syntax found: 11
Result: ready for review
```

## 10. Business end-to-end validation

Команда:

```bash
curl -X POST http://localhost:8080/projects/analyze \
  -H 'Content-Type: application/json' \
  -d '{"project_title":"Defense E2E Allergy App","project_description":"Команда из двух человек хочет сделать мобильное приложение с картой кафе для людей с аллергией, без глютена и без лактозы. Начать планируют с Турции и потом расширяться на другие страны. Есть полгода, важна модерация данных и надежность рекомендаций."}'
```

Фактический результат:

```text
task_id: 2caec3d9-213d-492d-8711-288cc7b5b2e0
project_title: Defense E2E Allergy App
published_to_kafka: true
event_bus: kafka_redpanda
```

Проверка отчета:

```bash
curl http://localhost:8080/reports/2caec3d9-213d-492d-8711-288cc7b5b2e0
```

Фактический результат:

```text
Матрица рисков: 4 риска
Название проекта: Defense E2E Allergy App
organizational: маленькая команда
data_quality: ошибки в данных о заведениях и аллергенах
schedule: ограниченный срок
product: широкий географический запуск
Critic / Validator Agent: approved
Количество доработок: 1
```

Вывод: бизнес-сценарий проходит через API Gateway, Kafka event bus, Risk Analysis Service и Report Service.

## 11. HAProxy Ingress E2E validation

Команда:

```bash
scripts/demo_ingress_e2e.sh
```

Фактический результат:

```text
GET /routes through HAProxy Ingress: 200 OK
POST /projects/analyze through HAProxy Ingress: published_to_kafka=true
GET /reports/{task_id} through HAProxy Ingress: risk matrix returned
```

Вывод: внешний путь проходит через HAProxy Ingress по host `risk-assistant.local`, а не только через
прямой port-forward на API Gateway.

## 12. Notes for defense

- Для live observability demo `networkPolicy.enabled=false`, чтобы Prometheus мог scrape'ить все микросервисы.
- Сам Helm template NetworkPolicy сохранен и может быть включен отдельно для демонстрации сетевой изоляции.
- Redpanda используется как локальная Kafka-compatible реализация; целевой production вариант описан через Strimzi Kafka.
- Karpenter заменен на Cluster Autoscaler, потому что локальный minikube не имеет cloud provider API для создания реальных node'ов; live autoscaler работает с KWOK provider config.
