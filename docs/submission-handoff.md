# Submission handoff

Дата актуализации: 2026-05-28.

Этот файл нужен как короткая карта сдачи: что открыть, что показать и какие команды быстро
подтверждают, что проект закрывает требования преподавателя.

## 1. Что это за проект

`Multi-Agent Risk Assistant` - микросервисная event-driven система для анализа проектных рисков.
Пользователь отправляет описание проекта, API Gateway принимает запрос, Project Intake публикует
событие в Kafka, Risk Analysis строит матрицу рисков, Report Service возвращает отчет, Audit Service
ведет журнал событий, Notification Service фиксирует готовность отчета.

В проекте 6 сервисов:

- `api-gateway`
- `project-intake-service`
- `risk-analysis-service`
- `report-service`
- `audit-service`
- `notification-service`

## 2. Что открыть первым

1. `README.md` - общая карта проекта.
2. `docs/criteria-matrix.md` - прямое соответствие требованиям преподавателя.
3. `docs/live-validation-report.md` - фактические live-проверки Kubernetes, ArgoCD, CI/CD,
   Prometheus, Locust и E2E.
4. `docs/real-usage-audit.md` - где каждый платформенный компонент реально используется.
5. `docs/teacher-qa.md` - короткие ответы на типовые вопросы.
6. `docs/high-level-scope.md` - ТЗ, User Stories, Use Cases, NFR, микросервисы, Kafka/EDA,
   данные, Redis-like cache, routing/rate limiting.
7. `docs/c4-and-sequence.md` - C4 L1-L3 и sequence diagram.

## 3. Что реализовано по максимуму

- ТЗ с ориентацией на ГОСТ 19/34, User Stories, Use Cases, NFR.
- C4 L1-L3, sequence diagram, OpenAPI, AsyncAPI, JSON schemas событий.
- 6 микросервисов, Kafka-compatible event bus, EDA, сравнение Kafka/RabbitMQ/NATS.
- RDBMS/NoSQL/cold storage design, Redis-like cache через Valkey/Redis-compatible слой.
- API Gateway, HAProxy Ingress, Keepalived, rate limiting.
- Kubernetes local cluster, Cilium CNI, Cluster Autoscaler manifest.
- Live Cluster Autoscaler deployment с KWOK provider config для локального стенда.
- Terraform namespaces/service accounts/secrets.
- ArgoCD App of Apps.
- Ansible role для Kafka через Strimzi и live Redpanda для локального Kafka API.
- Istio policies: retry, outlier detection, circuit breaker.
- Observability: Prometheus, Grafana dashboard, alerting, Loki/Tempo/OpenTelemetry manifests,
  сравнение альтернатив.
- CI/CD: GitLab Runner values, Kaniko job внутри Kubernetes, local CI pipeline с
  build/publish/GitOps/ArgoCD sync.
- Helm chart для 6 микросервисов с Kafka, cache и data-store настройками.
- Locust load test, circuit breaker demo, Grafana/Prometheus validation.

## 4. Live proof

Фактически проверено на локальном Kubernetes-стенде:

```text
Kubernetes nodes: 2 Ready
ArgoCD apps: risk-assistant-root, risk-assistant, kafka, platform-infra, observability = Synced/Healthy
Microservices: 6 deployed
Image: localhost:5000/risk-assistant:ci-final-demo
Prometheus scrape: 10/10 risk-assistant targets healthy
Locust normal run: 859 requests, 0 failures
E2E: POST /projects/analyze publishes to Kafka and GET /reports/{task_id} returns risk matrix
Circuit breaker demo: report-service outage and restore validated
Live Kaniko job: in-cluster registry tags latest, ci-kaniko-live
HAProxy Ingress E2E: /routes, /projects/analyze, /reports/{task_id}
```

## 5. Быстрая перепроверка

Без live-кластера:

```bash
python3 scripts/check_submission.py
.venv/bin/python -m pytest -q
```

Live-стенд:

```bash
scripts/defense_smoke.sh
START_PORT_FORWARD=1 scripts/demo_e2e.sh
scripts/demo_ingress_e2e.sh
scripts/live_kaniko_pipeline.sh
```

API Gateway:

```bash
kubectl --context risk-assistant -n risk-assistant port-forward svc/api-gateway 8080:8088
curl http://localhost:8080/routes
```

E2E:

```bash
curl -X POST http://localhost:8080/projects/analyze \
  -H 'Content-Type: application/json' \
  -d '{"project_title":"Defense E2E Allergy App","project_description":"Команда из двух человек хочет сделать мобильное приложение с картой кафе для людей с аллергией, без глютена и без лактозы. Начать планируют с Турции и потом расширяться на другие страны. Есть полгода, важна модерация данных и надежность рекомендаций."}'
```

## 6. Честные оговорки

- Для локального стенда используется Redpanda как Kafka-compatible broker, потому что он легче
  для Minikube. В документах и Ansible role описан целевой Kafka/Strimzi вариант.
- Karpenter для локального кластера не подходит так же естественно, как для облака, поэтому
  поднят Cluster Autoscaler с KWOK provider config. Он показывает рабочий autoscaler-контроллер,
  но не заменяет cloud/Cluster API provisioning реальных нод.
- В live GitOps используется локальный Git daemon, чтобы ArgoCD мог синхронизироваться без внешнего
  Git-хостинга.
- GitLab Runner зарегистрирован в GitLab project runner и работает в namespace `cicd`; runner token
  нельзя хранить в git, поэтому в репозитории должен оставаться плейсхолдер/пример, а реальный
  секрет задается локально при установке Helm chart.
