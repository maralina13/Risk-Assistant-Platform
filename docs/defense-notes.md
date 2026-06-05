# Шпаргалка для защиты

## 1. Короткое описание проекта

Multi-Agent Risk Assistant - это микросервисная платформа для анализа проектных рисков. Пользователь отправляет описание проекта, система создает задачу, публикует событие в Kafka, запускает многоагентный анализ, сохраняет отчет и дает доступ к статусу, результату и audit trail.

## 2. Почему микросервисы

Проект естественно делится на разные ответственности:

- API Gateway отвечает за входной трафик, маршрутизацию и rate limit.
- Project Intake Service валидирует заявку и создает задачу.
- Risk Analysis Service выполняет долгую и тяжелую обработку.
- Report Service отвечает за выдачу готового отчета.
- Audit Service хранит историю событий.
- Notification Service отправляет уведомления.

Такое разделение позволяет независимо масштабировать тяжелый анализ, не перегружая входной API и сервис отчетов.

## 3. Почему Kafka

Kafka выбрана не потому, что она самая простая, а потому что она лучше всего демонстрирует production-like EDA:

- события можно хранить и перечитывать;
- consumer groups позволяют масштабировать обработку;
- partitions помогают распределять нагрузку;
- consumer lag удобно показывать в Grafana;
- Strimzi хорошо подходит для Kubernetes.

Для маленького MVP проще был бы RabbitMQ или NATS JetStream. Это честный trade-off: Kafka сложнее в эксплуатации, но лучше подходит для аудита, replay и демонстрации платформенных требований.

## 4. Где здесь EDA

Project Intake Service не вызывает Risk Analysis Service напрямую как обязательную зависимость. Он публикует `ProjectSubmitted`, а Risk Analysis Service читает событие из Kafka. Audit Service и Notification Service тоже могут подписываться на события без изменения Project Intake Service. Это снижает связность и упрощает расширение системы.

## 5. Почему несколько хранилищ

- PostgreSQL: задачи, проекты, статусы, транзакционные данные.
- MongoDB: отчеты и audit-like документы, потому что структура результата может меняться.
- MinIO/S3-compatible cold storage в целевой схеме: архив отчетов и сырые agent outputs.
- Valkey/Redis: быстрые TTL counters для rate limiting и горячий cache.

## 6. Как объяснить routing layer

Есть несколько уровней:

1. HAProxy/Ingress принимает внешний трафик и балансирует вход.
2. API Gateway маршрутизирует бизнес-запросы к нужным сервисам.
3. Rate limiter защищает систему от перегрузки.
4. Istio управляет внутренними retry, circuit breaker и outlier detection.
5. Keepalived дает отказоустойчивый VIP для bare-metal/local lab сценария.

## 7. Почему Istio

Istio выбран из-за Envoy sidecar и готовых механизмов:

- retry policies;
- circuit breaker через connection pool и outlier detection;
- mTLS между сервисами;
- метрики `istio_requests_total` и latency histograms для Grafana;
- удобная демонстрация деградации сервиса при нагрузочном тесте.

Linkerd проще, но Istio лучше покрывает учебные критерии по traffic management.

## 8. Почему Cluster Autoscaler, а не Karpenter

Karpenter раскрывается в облаке, где он может создавать реальные ноды через cloud provider API. Для локального стенда проще и честнее показать Cluster Autoscaler как стандартный autoscaling controller. В документации отмечено, что в managed cloud Karpenter был бы хорошей альтернативой.

## 9. Observability stack

Выбран стек:

- Prometheus для метрик;
- Loki для логов;
- Tempo + OpenTelemetry Collector для трейсов;
- Grafana для визуализации;
- Alertmanager для алертов.

ELK и VictoriaMetrics/VictoriaLogs рассмотрены как альтернативы. ELK тяжелее для локального стенда, VictoriaMetrics хорош для production/high-cardinality, но для учебного стенда Prometheus проще и привычнее.

## 10. Как показать проверку Circuit Breaker

Сценарий:

1. Запустить Locust, чтобы генерировать трафик.
2. Во время теста масштабировать `report-service` до 0 или заставить его возвращать 5xx.
3. Проверить, что Istio retries пытаются повторить запрос.
4. После нескольких ошибок outlier detection исключает endpoint.
5. В Grafana видны 5xx/503, latency и retry behavior.

Команды:

```bash
locust -f tests/load/locustfile.py --host http://localhost:8080 \
  --headless --users 15 --spawn-rate 5 --run-time 70s --only-summary
DOWN_SECONDS=20 scripts/demo_circuit_breaker.sh
```

Фактически на live-стенде проверено: `report-service` масштабировался до `0`, во время отказа
на маршруте отчетов появились временные ошибки, затем deployment вернулся в `2/2 Running`.

## 11. Что проверено live

- Kubernetes cluster: 2 node, обе `Ready`.
- Cilium, Istio, HAProxy, Kafka/Redpanda, ArgoCD, Prometheus, Grafana, Alertmanager: Running.
- ArgoCD App of Apps: 5 приложений `Synced / Healthy`.
- 6 микросервисов: развернуты с image `localhost:5000/risk-assistant:ci-final-demo`.
- CI/CD: `scripts/local_ci_pipeline.sh` выполнил tests, build, GitOps update, ArgoCD sync и rollout validation.
- Prometheus: 10/10 targets из `risk-assistant` healthy.
- Locust: 859 requests, 0 failures на штатном прогоне; rate limiter отдавал `429` на жестком прогоне.

## 12. Что запустить локально

```bash
docker compose -f docker-compose.architecture.yml up --build
curl http://localhost:8080/routes
```

Потом отправить проект:

```bash
curl -X POST http://localhost:8080/projects/analyze \
  -H 'Content-Type: application/json' \
  -d '{"project_title":"Allergy travel app","project_description":"Команда разрабатывает сервис для путешественников с аллергиями: карта заведений, фильтры по аллергенам, отзывы, модерация и расширение на несколько стран."}'
```

## 13. Если спросят, что не является production-ready

Честный ответ:

- локальный docker-compose использует Redpanda вместо полноценного Kafka кластера;
- secrets в учебном Terraform заданы демонстрационно, в production нужен Vault/SOPS/External Secrets;
- Mongo/PostgreSQL/Valkey в Helm chart упрощены, в production лучше использовать operators или managed services;
- autoscaling нод локально ограничен возможностями локального кластера;
- LLM workflow в MVP может работать в mock mode для воспроизводимости тестов.

Это не минусы проекта, а нормальное разделение между учебным MVP и production hardening.
