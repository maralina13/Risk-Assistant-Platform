# C4 и Sequence Diagram

Диаграммы написаны в Mermaid, чтобы их можно было вставить в README, GitLab/GitHub Wiki или отчет.

## C4 L1 - System Context

```mermaid
C4Context
    title Multi-Agent Risk Assistant - System Context
    Person(user, "Пользователь", "Студент, аналитик или руководитель проекта")
    Person(admin, "Администратор платформы", "Поддерживает кластер, GitOps и observability")
    System(riskAssistant, "Multi-Agent Risk Assistant", "Анализирует описание проекта и формирует отчет по рискам")
    System_Ext(git, "Git Repository", "Хранит код, Helm charts и GitOps manifests")
    System_Ext(registry, "Local Container Registry", "Хранит Docker images")
    System_Ext(alerts, "Alert Receiver", "Email/Telegram/Slack для алертов")

    Rel(user, riskAssistant, "Отправляет проект, смотрит статус и отчет", "HTTPS/JSON")
    Rel(admin, riskAssistant, "Наблюдает и управляет", "Grafana/ArgoCD/kubectl")
    Rel(git, riskAssistant, "GitOps sync", "ArgoCD")
    Rel(riskAssistant, registry, "Получает images", "OCI")
    Rel(riskAssistant, alerts, "Отправляет алерты", "Alertmanager")
```

## C4 L2 - Container Diagram

```mermaid
C4Container
    title Multi-Agent Risk Assistant - Containers
    Person(user, "Пользователь")
    Container_Boundary(k8s, "Kubernetes cluster") {
        Container(lb, "HAProxy/Ingress", "Ingress Controller", "TLS termination, балансировка, entry point")
        Container(gateway, "API Gateway", "Python HTTP service", "Routing, rate limiting")
        Container(intake, "Project Intake Service", "Python HTTP service", "Прием заявки и создание задачи")
        Container(analysis, "Risk Analysis Service", "Python worker/http", "Многоагентный анализ")
        Container(report, "Report Service", "Python HTTP service", "Выдача отчетов")
        Container(audit, "Audit Service", "Python HTTP service/consumer", "Audit trail")
        Container(notification, "Notification Service", "Python consumer", "Уведомления")
        ContainerDb(kafka, "Kafka", "Strimzi Kafka", "Domain events")
        ContainerDb(postgres, "PostgreSQL", "RDBMS", "Projects and task status")
        ContainerDb(mongo, "MongoDB", "NoSQL", "Reports and audit docs")
        ContainerDb(valkey, "Valkey", "Redis-like cache", "Rate limit counters and hot cache")
        Container(obs, "Observability stack", "Prometheus/Loki/Tempo/Grafana", "Metrics, logs, traces, alerts")
    }

    Rel(user, lb, "Uses", "HTTPS")
    Rel(lb, gateway, "Routes", "HTTP")
    Rel(gateway, valkey, "Checks rate limit", "RESP")
    Rel(gateway, intake, "POST /projects/analyze", "HTTP")
    Rel(gateway, report, "GET /reports/{id}", "HTTP")
    Rel(gateway, audit, "GET /admin/audit/events", "HTTP")
    Rel(intake, postgres, "Writes task", "SQL")
    Rel(intake, kafka, "Publishes ProjectSubmitted", "Kafka protocol")
    Rel(analysis, kafka, "Consumes ProjectSubmitted, publishes analysis events", "Kafka protocol")
    Rel(analysis, postgres, "Updates task status", "SQL")
    Rel(analysis, mongo, "Stores report draft/artifacts", "Mongo protocol")
    Rel(report, mongo, "Reads report", "Mongo protocol")
    Rel(audit, kafka, "Consumes all events", "Kafka protocol")
    Rel(notification, kafka, "Consumes ReportGenerated, publishes NotificationSent", "Kafka protocol")
    Rel(gateway, obs, "Emits telemetry", "OTLP/Prometheus")
```

## C4 L3 - Component Diagram для Risk Analysis Service

```mermaid
C4Component
    title Risk Analysis Service - Components
    Container_Boundary(analysis, "Risk Analysis Service") {
        Component(http, "Internal HTTP Handler", "Python BaseHTTPServer", "Ручной запуск обработки и health endpoints")
        Component(worker, "Kafka Worker", "Thread + KafkaConsumer", "Читает ProjectSubmitted")
        Component(orchestrator, "Agent Workflow Orchestrator", "Python module", "Запускает цепочку агентов")
        Component(reqAgent, "Requirement Analyst Agent", "LLM/mock step", "Извлекает требования")
        Component(riskAgent, "Risk Analyst Agent", "LLM/mock step", "Находит риски")
        Component(planAgent, "Mitigation Planner Agent", "LLM/mock step", "Готовит план снижения")
        Component(criticAgent, "Critic Validator Agent", "LLM/mock step", "Проверяет качество")
        Component(writerAgent, "Report Writer Agent", "LLM/mock step", "Формирует markdown")
        Component(storage, "Storage Adapter", "Python module", "Запись статусов и отчетов")
        Component(events, "Event Factory", "Python module", "Создает доменные события")
    }
    ContainerDb(kafka, "Kafka")
    ContainerDb(postgres, "PostgreSQL")
    ContainerDb(mongo, "MongoDB")

    Rel(kafka, worker, "ProjectSubmitted")
    Rel(http, orchestrator, "process_task")
    Rel(worker, orchestrator, "process_task")
    Rel(orchestrator, reqAgent, "1")
    Rel(orchestrator, riskAgent, "2")
    Rel(orchestrator, planAgent, "3")
    Rel(orchestrator, criticAgent, "4")
    Rel(orchestrator, writerAgent, "5")
    Rel(orchestrator, storage, "save status/report")
    Rel(orchestrator, events, "create events")
    Rel(storage, postgres, "task status")
    Rel(storage, mongo, "report")
    Rel(events, kafka, "RiskAnalysisStarted/Completed/Failed")
```

## Sequence Diagram - успешный анализ

```mermaid
sequenceDiagram
    autonumber
    actor U as Пользователь
    participant LB as HAProxy/Ingress
    participant GW as API Gateway
    participant RL as Valkey Rate Limiter
    participant PI as Project Intake Service
    participant PG as PostgreSQL
    participant K as Kafka
    participant RA as Risk Analysis Service
    participant M as MongoDB
    participant RS as Report Service
    participant AU as Audit Service
    participant N as Notification Service

    U->>LB: POST /projects/analyze
    LB->>GW: proxy request
    GW->>RL: INCR rate-limit:{client}
    RL-->>GW: allowed
    GW->>PI: POST /projects/analyze
    PI->>PG: INSERT project, analysis_task
    PI->>K: publish ProjectSubmitted
    PI-->>GW: 202 task_id
    GW-->>U: 202 task_id
    K-->>RA: consume ProjectSubmitted
    RA->>K: publish RiskAnalysisStarted
    RA->>PG: UPDATE status=running
    RA->>RA: run multi-agent workflow
    RA->>M: save report
    RA->>PG: UPDATE status=completed
    RA->>K: publish RiskAnalysisCompleted
    RA->>K: publish ReportGenerated
    K-->>AU: consume all events
    K-->>N: consume ReportGenerated
    N->>K: publish NotificationSent
    U->>LB: GET /reports/{task_id}
    LB->>GW: proxy request
    GW->>RS: GET /reports/{task_id}
    RS->>M: find report
    RS-->>GW: report markdown
    GW-->>U: report markdown
```

## Sequence Diagram - circuit breaker при отказе Report Service

```mermaid
sequenceDiagram
    autonumber
    actor U as Пользователь
    participant GW as API Gateway
    participant I as Istio Sidecar
    participant RS as Report Service
    participant IS as Istio Outlier Detection

    U->>GW: GET /reports/{task_id}
    GW->>I: HTTP request to report-service
    I->>RS: try #1
    RS--xI: 5xx / timeout
    I->>RS: retry
    RS--xI: 5xx / timeout
    I->>IS: count consecutive errors
    IS-->>I: eject unhealthy endpoint
    I-->>GW: 503 after retry budget
    GW-->>U: degraded response
```

