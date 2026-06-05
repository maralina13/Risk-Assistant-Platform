# Demo scenario

Этот сценарий нужен, чтобы быстро показать проект преподавателю: сначала документы и архитектуру, затем локальный MVP, затем платформенную часть.

## 1. Что открыть первым

1. `README.md` - карта проекта.
2. `docs/criteria-matrix.md` - доказательство соответствия критериям.
3. `docs/high-level-scope.md` - ТЗ, User Stories, Use Cases, NFR, EDA и выбор Kafka.
4. `docs/c4-and-sequence.md` - C4 L1-L3 и sequence diagrams.
5. `docs/platform-implementation.md` - Kubernetes, GitOps, mesh, observability, CI/CD, testing.
6. `docs/defense-notes.md` - короткие ответы на вопросы.
7. `docs/teacher-qa.md` - ответы на вероятные вопросы преподавателя.
8. `docs/live-validation-report.md` - фактический live-статус Kubernetes, ArgoCD, CI/CD, Prometheus и Locust.
9. `docs/real-usage-audit.md` - где каждый платформенный компонент реально используется.
10. `docs/adr/` - формальные записи архитектурных решений.

## 2. Self-check без внешних зависимостей

```bash
python3 scripts/check_submission.py
```

Ожидаемый результат:

```text
Submission self-check
[ OK ] Required files present
[ OK ] JSON files are valid
[ OK ] Python files compile
[ OK ] Documentation contains required architecture terms
[ OK ] Microservice directories found
Result: ready for review
```

## 3. Локальный MVP через Docker Compose

```bash
docker compose -f docker-compose.architecture.yml up --build
```

Проверить маршруты:

```bash
curl http://localhost:8080/routes
```

Отправить проект:

```bash
curl -X POST http://localhost:8080/projects/analyze \
  -H 'Content-Type: application/json' \
  -d '{"project_title":"Allergy travel app","project_description":"Команда разрабатывает сервис для путешественников с аллергиями: карта заведений, фильтры по аллергенам, отзывы, модерация и расширение на несколько стран."}'
```

Проверить audit events:

```bash
curl http://localhost:8080/admin/audit/events
```

## 4. Как показать rate limiting

API Gateway ограничивает количество запросов к `POST /projects/analyze`. Быстрый способ показать:

```bash
for i in 1 2 3 4 5 6; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8080/projects/analyze \
    -H 'Content-Type: application/json' \
    -d '{"project_title":"Rate limit demo","project_description":"Длинное описание проекта для демонстрации rate limiting на уровне API Gateway через Valkey или memory fallback."}'
done
```

Ожидаемо один из ответов будет `429`, если лимит уже исчерпан в текущем окне.

## 5. Kubernetes/GitOps walkthrough

Показывать как целевой production-like контур:

1. `infra/terraform/main.tf` - namespaces, service account, secrets.
2. `infra/argocd/root-app.yaml` - App of Apps.
3. `infra/ansible/roles/strimzi-kafka/` - роль Strimzi Kafka.
4. `infra/helm/risk-assistant/` - chart для всех микросервисов.
5. `infra/kubernetes/mesh/istio-policies.yaml` - retry, circuit breaker, outlier detection.
6. `infra/kubernetes/gateway/` - HAProxy ingress, Keepalived, rate limit.
7. `infra/observability/` - Prometheus, Loki, Tempo, OpenTelemetry, Grafana, alerts.
8. `infra/ci/gitlab-ci.yml` - Kaniko build, push, Helm update, ArgoCD sync.
9. `scripts/local_ci_pipeline.sh` - live CI/CD demo без внешнего GitLab.
10. `scripts/live_kaniko_pipeline.sh` - live Kaniko build внутри Kubernetes с push в in-cluster registry.

Live-команды:

```bash
kubectl get nodes
kubectl -n argocd get applications.argoproj.io
kubectl -n risk-assistant get deploy api-gateway project-intake-service risk-analysis-service report-service audit-service notification-service \
  -o 'custom-columns=NAME:.metadata.name,READY:.status.readyReplicas,IMAGE:.spec.template.spec.containers[0].image'
```

Ожидаемый результат:

```text
ArgoCD apps: Synced / Healthy
microservice image: localhost:5000/risk-assistant:ci-final-demo
```

## 6. Быстрый Kubernetes smoke

```bash
scripts/defense_smoke.sh
```

Что показать:

- 2 Kubernetes node `Ready`;
- ArgoCD applications `Synced / Healthy`;
- 6 микросервисов развернуты;
- Kafka, Istio, Cilium и observability ресурсы доступны;
- self-check завершается `Result: ready for review`.

## 7. CI/CD live demo

Локальный GitOps pipeline:

```bash
IMAGE_TAG=ci-final-demo scripts/local_ci_pipeline.sh
```

Что показать:

- `10 passed`;
- Docker image build;
- update GitOps image tag;
- ArgoCD sync;
- rollout validation.

Kaniko внутри Kubernetes:

```bash
scripts/live_kaniko_pipeline.sh
```

Что показать:

- `risk-assistant-kaniko-live condition met`;
- registry response содержит теги `latest` и `ci-kaniko-live`;
- образ пушится в `cicd-registry.cicd.svc.cluster.local:5000`.

## 8. HAProxy Ingress E2E

```bash
scripts/demo_ingress_e2e.sh
```

Что показать:

- `/routes` отвечает через host `risk-assistant.local`;
- `POST /projects/analyze` возвращает `published_to_kafka: true`;
- `GET /reports/{task_id}` возвращает готовый markdown-отчет.

## 9. Observability live demo

```bash
kubectl -n risk-assistant get servicemonitor
kubectl -n observability get prometheusrule risk-assistant-alerts
kubectl -n observability get configmap risk-assistant-grafana-dashboard
```

Проверка логов и трейсов:

```bash
scripts/validate_observability_deep.sh
```

Что показать:

- Loki отвечает `ready`;
- Loki query возвращает `defense observability log`;
- Tempo отвечает `ready`;
- OTel Collector принимает `/v1/traces`;
- Tempo возвращает trace по `/api/traces/{trace_id}`.

Для Prometheus:

```bash
kubectl -n observability port-forward svc/monitoring-kube-prometheus-prometheus 19090:9090
curl 'http://localhost:19090/api/v1/query?query=sum(risk_assistant_service_up)'
```

Ожидаемо:

```text
sum(risk_assistant_service_up): 10
```

## 10. E2E demo одной командой

Если API Gateway еще не проброшен на localhost, команда сама поднимет port-forward:

```bash
START_PORT_FORWARD=1 scripts/demo_e2e.sh
```

Что показать в выводе:

- `/routes` показывает маршруты API Gateway;
- `POST /projects/analyze` возвращает `task_id`, `published_to_kafka: true`;
- `GET /reports/{task_id}` возвращает матрицу рисков и approved validation.

## 11. Cluster Autoscaler demo

```bash
scripts/demo_cluster_autoscaler.sh
```

Что показать:

- demo workload `autoscaler-probe` получает `Pending`;
- Cluster Autoscaler видит `4 unschedulable pods left`;
- в локальном Minikube вывод честно заканчивается `No expansion options`, потому что нет cloud/Cluster API provider для создания реальных нод.

## 12. Load test и Circuit Breaker

Запуск Locust:

```bash
locust -f tests/load/locustfile.py --host http://localhost:8080 \
  --headless --users 25 --spawn-rate 5 --run-time 45s --only-summary
```

Проверка circuit breaker в Kubernetes:

```bash
DOWN_SECONDS=20 scripts/demo_circuit_breaker.sh
```

Что смотреть в Grafana:

- рост 5xx/503;
- P95 latency;
- rate limiter 429;
- Kafka consumer lag;
- recovery после возврата `report-service`.

## 13. Что сказать, если спросят про ограничения

- Redpanda используется как Kafka-compatible broker для live Minikube; целевой Kafka/Strimzi вариант есть в Ansible role и manifests.
- GitLab Runner values готовы, но регистрация runner требует GitLab URL/token; поэтому live build демонстрируется Kubernetes Kaniko Job.
- Cluster Autoscaler в Minikube установлен и анализирует pending pods, но реальные ноды создаются только при наличии cloud/Cluster API/Talos/k3s provisioner.
- Keepalived работает как DaemonSet; полноценный VIP с доступом напрямую с macOS host требует L2/bare-metal сети.
