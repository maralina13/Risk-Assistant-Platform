# High-level scope: Multi-Agent Risk Assistant

## 0. Приветствие

Большой привет от преподавателя и пожелание успехов.

## 1. Техническое задание, ключевые пункты по ГОСТ 19/34

### 1.1 Наименование системы

Multi-Agent Risk Assistant - распределенная система анализа проектных рисков с использованием многоагентного LLM workflow.

### 1.2 Основание для разработки

Учебный проект по проектированию микросервисной, событийно-ориентированной и Kubernetes-native платформы. Система должна демонстрировать сервисную декомпозицию, асинхронное взаимодействие через брокер сообщений, хранение данных в нескольких типах СУБД, кэширование, routing layer, observability, CI/CD и нагрузочную валидацию.

### 1.3 Назначение

Система принимает описание проекта, запускает многоагентный анализ требований и рисков, формирует отчет, сохраняет артефакты и предоставляет пользователю статус обработки и готовый результат.

### 1.4 Пользователи

- Студент/аналитик: отправляет описание проекта и получает отчет по рискам.
- Руководитель проекта: смотрит итоговый отчет, критичные риски и mitigation plan.
- Администратор платформы: управляет деплоем, наблюдаемостью, лимитами и отказоустойчивостью.

### 1.5 Основные функции

- Прием описания проекта через API Gateway.
- Валидация входных данных и постановка задачи в обработку.
- Публикация доменных событий в Kafka topics.
- Многоагентный анализ: требования, риски, план снижения, критика/валидация, отчет.
- Хранение задач в PostgreSQL, отчетов и audit trail в MongoDB, лимитов/горячего состояния в Valkey/Redis.
- Получение статуса задачи и готового отчета через HTTP API.
- Аудит событий и базовая трассируемость через correlation id.

### 1.6 Требования к архитектуре

- Архитектура: микросервисная, event-driven.
- Минимум 3 микросервиса: в проекте 5 прикладных микросервисов + API Gateway.
- Сервисная сеть: Istio для retry, circuit breaker и outlier detection.
- Входной слой: маршрутизатор/API Gateway, балансировщик, rate limiter.
- Инфраструктура: Kubernetes, Cilium CNI, Cluster Autoscaler, ArgoCD, Terraform, Ansible, Helm.
- Наблюдаемость: метрики, логи, трейсы, alerting.

### 1.7 Требования к надежности

- Повторные попытки между сервисами на уровне service mesh.
- Circuit breaker для деградирующих сервисов.
- Асинхронная обработка через Kafka для снижения связности.
- Audit trail для восстановления истории обработки.
- Горизонтальное масштабирование stateless сервисов через Kubernetes HPA.

### 1.8 Требования к эксплуатации

- Все приложения разворачиваются Helm chart'ом.
- Инфраструктурные namespace, service accounts и базовые secrets описаны Terraform.
- Kafka разворачивается Ansible Role через Strimzi operator.
- ArgoCD использует App of Apps pattern.
- CI/CD собирает образы Kaniko, пушит в локальный registry, обновляет Helm values и синхронизирует ArgoCD.

### 1.9 Ограничения

- Локальная инфраструктура учебная: Minikube/k3s/k0s/Talos допускаются.
- Для локального docker-compose используется Redpanda как легкий Kafka-compatible broker, но целевая Kubernetes-схема использует Kafka через Strimzi.
- LLM workflow в MVP может работать в mock mode для воспроизводимых тестов.

## 2. User Stories

### US-1. Отправка проекта на анализ

Как студент, я хочу отправить описание проекта через API, чтобы система начала анализ рисков и вернула идентификатор задачи.

Критерии приемки:
- API принимает `project_title` и `project_description`.
- Слишком короткое описание отклоняется.
- При успешной отправке возвращается `task_id`.
- Создается событие `ProjectSubmitted`.

### US-2. Получение статуса

Как пользователь, я хочу получить статус задачи, чтобы понимать, идет анализ или отчет уже готов.

Критерии приемки:
- По `task_id` возвращается статус `pending`, `running`, `completed` или ошибка.
- При неизвестном `task_id` возвращается 404.

### US-3. Получение отчета

Как руководитель проекта, я хочу получить markdown-отчет по рискам, чтобы принять решение по дальнейшим действиям.

Критерии приемки:
- По `task_id` возвращается отчет.
- Если отчета еще нет, возвращается 404.
- Отчет содержит матрицу рисков и план mitigation.

### US-4. Аудит обработки

Как администратор, я хочу видеть события обработки, чтобы расследовать сбои и проверять SLA.

Критерии приемки:
- Audit service хранит события ключевых этапов.
- События связаны через `correlation_id`.
- Доступен endpoint просмотра audit events.

### US-5. Защита от перегрузки

Как владелец платформы, я хочу ограничивать частоту запросов, чтобы один клиент не перегружал анализатор.

Критерии приемки:
- API Gateway применяет rate limit.
- Backend лимитера - Valkey/Redis.
- При превышении лимита возвращается HTTP 429.

## 3. Use Cases

### UC-1. Запуск анализа

Основной сценарий:
1. Пользователь отправляет `POST /projects/analyze`.
2. Load Balancer передает запрос в API Gateway.
3. API Gateway проверяет rate limit в Valkey.
4. API Gateway маршрутизирует запрос в Project Intake Service.
5. Project Intake Service сохраняет задачу в PostgreSQL.
6. Project Intake Service публикует `ProjectSubmitted` в Kafka.
7. Risk Analysis Service читает событие и запускает workflow.
8. Risk Analysis Service публикует `RiskAnalysisStarted`, затем `RiskAnalysisCompleted` или `RiskAnalysisFailed`.
9. Report Service сохраняет/отдает отчет.
10. Audit Service сохраняет историю событий.

Альтернативы:
- A1: описание короче 30 символов -> HTTP 400.
- A2: rate limit превышен -> HTTP 429.
- A3: Risk Analysis Service недоступен -> Kafka сохраняет событие до восстановления consumer group.

### UC-2. Получение отчета

Основной сценарий:
1. Пользователь отправляет `GET /reports/{task_id}`.
2. API Gateway маршрутизирует запрос в Report Service.
3. Report Service ищет отчет в MongoDB/локальном runtime storage.
4. Система возвращает markdown-отчет.

Альтернативы:
- A1: отчет еще не создан -> HTTP 404.
- A2: Report Service деградирует -> Istio retry + circuit breaker.

### UC-3. Операционный мониторинг

Основной сценарий:
1. OpenTelemetry Collector собирает traces/metrics/logs.
2. Prometheus/VictoriaMetrics хранит метрики.
3. Loki/VictoriaLogs хранит логи.
4. Grafana показывает latency, Kafka consumer lag, rate limiter hits, service errors.
5. Alertmanager отправляет alert при превышении порогов.

## 4. NFR

| Категория | Требование |
| --- | --- |
| Производительность | P95 latency для `POST /projects/analyze` до постановки задачи: <= 500 ms без учета LLM обработки. |
| Масштабируемость | Stateless сервисы масштабируются горизонтально через replicas/HPA; Kafka consumer groups масштабируют обработку событий. |
| Надежность | Ошибка одного consumer не теряет событие; Kafka хранит сообщения до подтверждения consumer group. |
| Отказоустойчивость | Istio retry/outlier detection исключает деградирующие pod'ы из трафика. |
| Безопасность | Внутренние сервисы не публикуются наружу; вход только через Gateway/Ingress; секреты вынесены в Kubernetes Secret. |
| Наблюдаемость | Метрики, логи, трейсы и алерты собираются централизованно. |
| Поддерживаемость | API описан OpenAPI, события - AsyncAPI/JSON Schema, инфраструктура - IaC/GitOps. |
| Совместимость | Локальный запуск через docker-compose, целевой запуск через Kubernetes/Helm. |

## 5. Микросервисы

| Сервис | Ответственность | HTTP | Kafka |
| --- | --- | --- | --- |
| API Gateway | Routing, rate limiting, единая точка входа | 8088 | - |
| Project Intake Service | Валидация заявки, создание задачи | 8091 | publish `ProjectSubmitted` |
| Risk Analysis Service | Многоагентный анализ рисков | 8092 | consume `ProjectSubmitted`, publish analysis events |
| Report Service | Выдача и хранение отчетов | 8093 | consume `RiskAnalysisCompleted`/`ReportGenerated` в целевой схеме |
| Audit Service | Audit trail событий | 8094 | consume all domain events |
| Notification Service | Уведомления о готовности отчета | 8095 | consume `ReportGenerated`, publish `NotificationSent` |

Минимум выполнен: 5 прикладных микросервисов. Для команды из 2 человек получается по 2+ микросервиса на человека: первый участник - API Gateway, Project Intake, Report; второй участник - Risk Analysis, Audit, Notification.

## 6. Kafka, RabbitMQ, NATS и EDA

### Почему EDA

Анализ рисков может быть долгим, а пользователю важно быстро получить `task_id`. Event-driven architecture разделяет прием запроса и тяжелую обработку. Сервисы становятся слабосвязанными: Project Intake не обязан знать, сколько downstream сервисов читают `ProjectSubmitted`.

### Сравнение брокеров

| Критерий | Kafka | RabbitMQ | NATS |
| --- | --- | --- | --- |
| Основная модель | Distributed commit log, topics, partitions | Message broker, queues/exchanges | Lightweight pub/sub, request-reply |
| Retention событий | Сильная сторона: события можно перечитать | Обычно сообщение исчезает после ack | JetStream дает persistence, но проще по модели |
| Consumer groups | Нативно и удобно для масштабирования | Есть competing consumers, но replay хуже | Есть queue groups |
| Audit/replay | Отлично подходит | Требует доп. паттернов | Возможен с JetStream |
| Latency | Хорошая, но не самая минимальная | Хорошая | Очень низкая |
| Операционная сложность | Выше | Средняя | Ниже |

### Почему выбрана Kafka

Kafka лучше всего подходит для учебной цели EDA: можно показать topics, partitions, consumer groups, retention, replay событий, consumer lag и интеграцию со Strimzi в Kubernetes. Для risk assistant важны аудит, повторное чтение событий, масштабирование анализа и метрики consumer lag.

### Что объективно лучше подошло бы для MVP

Для маленького локального MVP без replay и долгого хранения событий объективно проще подошел бы NATS JetStream или RabbitMQ: меньше операционная нагрузка, проще запуск, ниже порог входа. Но для демонстрации production-like платформы, GitOps, observability и Kafka latency/queue dashboards Kafka обоснованнее.

## 7. Данные

| Тип | Технология | Что хранит | Причина |
| --- | --- | --- | --- |
| RDBMS | PostgreSQL | projects, analysis_tasks, статусы | Транзакционность, связи, SQL-запросы |
| NoSQL hot/warm | MongoDB | отчеты, audit documents | Гибкая структура markdown/JSON отчетов |
| Cold storage | S3-compatible MinIO в целевой схеме | архив отчетов, сырые agent outputs | Дешевое объектное хранение больших артефактов |
| Cache | Valkey/Redis | rate limit counters, hot status cache | TTL, атомарные counters, быстрый доступ |

## 8. Routing layer

- Маршрутизатор: API Gateway на уровне приложения.
- Балансировщик: HAProxy Ingress Controller или Nginx/HAProxy перед gateway.
- Rate Limiter: Valkey/Redis-backed лимитер в API Gateway; в Kubernetes также добавлен Envoy/Istio слой для gateway-level ограничений.
- Отказоустойчивость входа: Keepalived VRRP для виртуального IP перед HAProxy в bare-metal/local lab сценарии.

