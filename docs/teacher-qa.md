# Teacher Q&A

Короткие ответы на вопросы, которые удобно держать рядом во время защиты.

## Почему это не монолит

Система разделена по разным темпам изменения и масштабирования. API Gateway и Project Intake
обрабатывают быстрые пользовательские запросы, Risk Analysis выполняет тяжелую обработку, Report
Service отвечает за чтение результатов, Audit и Notification расширяют поведение через события.
Такой дизайн позволяет масштабировать анализ отдельно от входного API.

## Где минимум 3 микросервиса

В проекте 6 сервисов: `api-gateway`, `project-intake-service`, `risk-analysis-service`,
`report-service`, `audit-service`, `notification-service`. В Helm chart они описаны как отдельные
Deployments и Services.

## Где Kafka и зачем она нужна

Project Intake публикует событие `ProjectSubmitted`, а Risk Analysis, Audit и Notification работают
как независимые event consumers/producers. Kafka выбрана из-за replay, retention, consumer groups,
partitioning и удобной observability через lag/throughput. Для маленького MVP RabbitMQ или NATS
были бы проще, но Kafka лучше показывает production-like EDA.

## Почему в live-стенде Redpanda

Redpanda совместима с Kafka API и легче для локального Minikube. Это практичный вариант для
демонстрации. Целевой вариант Kafka через Strimzi описан в Ansible role и Kubernetes manifests.

## Где RDBMS и NoSQL

PostgreSQL используется для транзакционных сущностей: projects, tasks, statuses. MongoDB подходит
для отчетов и audit-документов с гибкой структурой. Cold storage в целевой архитектуре нужен для
архивов отчетов и сырых agent outputs.

## Где Redis-like cache

Valkey/Redis-compatible слой используется для rate limiting и быстрых TTL counters. Если Valkey
недоступен в локальном запуске, API Gateway может работать через memory fallback, но в Kubernetes
поднимается Valkey.

## Где router, balancer и rate limiter

Router - `api-gateway`. Balancer/entrypoint - HAProxy Ingress и Kubernetes Service balancing.
Keepalived описан для отказоустойчивого VIP. Rate limiting есть на уровне Gateway/API и
инфраструктурно описан в `infra/kubernetes/gateway/rate-limit.yaml`.

## Где Service Mesh

Istio policies лежат в `infra/kubernetes/mesh/istio-policies.yaml`: retry, outlier detection и
circuit breaker настройки. В live-кластере `istiod` запущен, sidecar injection включен для
микросервисов.

## Где Observability

Prometheus собирает метрики через ServiceMonitor, Grafana получает dashboard ConfigMap,
PrometheusRule задает alerting. Loki, Tempo и OpenTelemetry Collector описаны как часть
наблюдаемости, а альтернативы VictoriaMetrics/VictoriaLogs/ELK/SigNoz разобраны в документации.

## Где CI/CD

`infra/ci/gitlab-ci.yml` описывает целевой pipeline с Kaniko, registry, Helm update и ArgoCD sync.
`scripts/local_ci_pipeline.sh` проверен live: тесты, Docker image, загрузка в Minikube, обновление
GitOps source, ArgoCD sync и rollout validation.

## Что показать, если времени мало

1. `docs/criteria-matrix.md`.
2. `docs/live-validation-report.md`.
3. `scripts/defense_smoke.sh`.
4. `START_PORT_FORWARD=1 scripts/demo_e2e.sh`.
5. `docs/c4-and-sequence.md`.

Этого достаточно, чтобы показать и архитектуру, и работающий стенд.
