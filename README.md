# Multi-Agent Risk Assistant

Большой привет от преподавателя и пожелание успехов.

Multi-Agent Risk Assistant - учебный проект микросервисной event-driven платформы для анализа проектных рисков. Пользователь отправляет описание проекта, система ставит задачу в обработку, запускает многоагентный workflow, сохраняет отчет и дает доступ к статусу, отчету и audit trail.

## Что смотреть преподавателю

| Критерий | Где находится |
| --- | --- |
| Live validation: Kubernetes, ArgoCD, CI/CD, Prometheus, Locust, E2E | `docs/live-validation-report.md` |
| Короткий handoff для сдачи | `docs/submission-handoff.md` |
| Ответы на вопросы преподавателя | `docs/teacher-qa.md` |
| High-level scope, ТЗ, User Story, Use Cases, NFR | `docs/high-level-scope.md` |
| C4 L1-L3 и Sequence Diagram | `docs/c4-and-sequence.md` |
| Полное покрытие Kubernetes/IaC/GitOps/Mesh/Observability/CI/CD/Testing | `docs/platform-implementation.md` |
| Матрица соответствия критериям | `docs/criteria-matrix.md` |
| Шпаргалка для защиты | `docs/defense-notes.md` |
| Быстрый чеклист защиты | `docs/defense-checklist.md` |
| Demo scenario | `docs/demo-scenario.md` |
| Architecture Decision Records | `docs/adr/` |
| Runbooks для live demo | `docs/runbooks/` |
| OpenAPI и AsyncAPI | `contracts/openapi.yaml`, `contracts/asyncapi.yaml` |
| Kafka topics и event schemas | `infra/kafka/topics.json`, `contracts/events/*.json` |
| Docker Compose архитектурного MVP | `docker-compose.architecture.yml` |
| Kubernetes manifests | `infra/kubernetes/` |
| Terraform | `infra/terraform/main.tf` |
| ArgoCD App of Apps | `infra/argocd/` |
| Ansible role для Strimzi Kafka | `infra/ansible/` |
| Helm chart 3+ микросервисов | `infra/helm/risk-assistant/` |
| Observability stack | `infra/observability/` |
| CI/CD Kaniko + Registry + Helm + ArgoCD | `infra/ci/gitlab-ci.yml`, `scripts/local_ci_pipeline.sh` |
| Locust load test | `tests/load/locustfile.py` |

## Live status

Стенд был поднят и проверен в Kubernetes:

- Minikube cluster: 2 node, обе `Ready`;
- Cilium CNI, Istio, HAProxy Ingress, Kafka-compatible Redpanda, ArgoCD, Prometheus, Grafana, Alertmanager: Running;
- ArgoCD App of Apps: `risk-assistant-root`, `risk-assistant`, `kafka`, `platform-infra`, `observability` = `Synced / Healthy`;
- 6 микросервисов развернуты с image `localhost:5000/risk-assistant:ci-final-demo`;
- Prometheus scrape: 10/10 targets healthy, `sum(risk_assistant_service_up)=10`;
- Locust: 859 requests, 0 failures на штатном прогоне;
- E2E: `POST /projects/analyze` публикует Kafka event, `GET /reports/{task_id}` возвращает отчет с матрицей рисков.

Подробные команды и фактические результаты: `docs/live-validation-report.md`.

## Архитектура MVP

В проекте есть 5 прикладных микросервисов и отдельный API Gateway:

- `api-gateway` - routing, rate limiting, единая точка входа.
- `project-intake-service` - прием проекта и создание задачи.
- `risk-analysis-service` - многоагентный анализ требований и рисков.
- `report-service` - выдача отчета.
- `audit-service` - audit trail событий.
- `notification-service` - уведомления о готовности отчета.

Асинхронная связность построена вокруг Kafka-compatible event bus. В локальном `docker-compose.architecture.yml` используется Redpanda как легкий Kafka API broker, в Kubernetes-целевой схеме используется Kafka через Strimzi.

## Быстрый локальный запуск

```bash
docker compose -f docker-compose.architecture.yml up --build
```

После запуска:

```bash
curl http://localhost:8080/routes
curl -X POST http://localhost:8080/projects/analyze \
  -H 'Content-Type: application/json' \
  -d '{"project_title":"Allergy travel app","project_description":"Команда разрабатывает сервис для путешественников с аллергиями: карта заведений, фильтры по аллергенам, отзывы и расширение на несколько стран."}'
```

## Проверки

Зависимости для локальных проверок:

```bash
python3 -m pip install -r requirements-dev.txt
```

```bash
make architecture-check
make docs-check
```

Проверка без `make`, `pytest` и `helm`:

```bash
python3 scripts/check_submission.py
```

Live/demo скрипты:

```bash
scripts/bootstrap_local_cluster.sh
scripts/deploy_platform.sh
scripts/validate_live_cluster.sh
scripts/defense_smoke.sh
START_PORT_FORWARD=1 scripts/demo_e2e.sh
scripts/demo_circuit_breaker.sh
IMAGE_TAG=ci-final-demo scripts/local_ci_pipeline.sh
```

Если установлен `helm`, можно проверить шаблонизацию chart:

```bash
make helm-template
```

Если установлен `locust`, можно запустить нагрузочный сценарий:

```bash
make load-test
```

## Kubernetes live demo

Если кластер уже поднят, открыть API Gateway:

```bash
kubectl -n risk-assistant port-forward svc/api-gateway 8080:8088
curl http://localhost:8080/routes
```

Показать GitOps:

```bash
kubectl -n argocd get applications.argoproj.io
```

Показать Prometheus/Grafana:

```bash
kubectl -n risk-assistant get servicemonitor
kubectl -n observability get prometheusrule risk-assistant-alerts
kubectl -n observability port-forward svc/monitoring-grafana 3000:80
```

Порядок для повторного разворачивания демонстрационного стенда:

1. Поднять локальный Kubernetes с Cilium.
2. Применить Terraform из `infra/terraform`.
3. Установить ArgoCD и применить `infra/argocd/root-app.yaml`.
4. Развернуть Kafka через Ansible роль `infra/ansible/roles/strimzi-kafka`.
5. Развернуть Istio policies, gateway/rate limit и observability manifests.
6. Деплоить приложение Helm chart'ом из `infra/helm/risk-assistant`.
7. Запустить Locust и проверить Grafana dashboards/alerts.

Подробные команды и обоснования лежат в `docs/platform-implementation.md`.
Пошаговые runbook'и для запуска лежат в `docs/runbooks/`.
