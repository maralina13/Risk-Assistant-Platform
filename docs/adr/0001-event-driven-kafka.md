# ADR-0001: Event-driven architecture with Kafka

## Status

Accepted.

## Context

Risk analysis is a long-running operation. The API should quickly accept a request and return `task_id`, while downstream services process the task asynchronously. The platform also needs auditability, replay, consumer lag metrics and clear integration with Kubernetes.

## Decision

Use event-driven architecture with Kafka topics:

- `project-events`;
- `analysis-events`;
- `report-events`;
- `audit-events`.

For local docker-compose use Redpanda as a lightweight Kafka-compatible broker. For Kubernetes use Strimzi Kafka.

## Alternatives

- RabbitMQ: simpler queues and routing, good for task distribution, weaker event replay model.
- NATS JetStream: very lightweight and fast, simpler operationally, but less common for Kafka-style replay and consumer lag demonstrations.
- Synchronous HTTP orchestration: simpler for MVP, but tightly couples services and hides EDA criteria.

## Consequences

Benefits:

- services are loosely coupled;
- events can be retained and replayed;
- analysis workers can scale through consumer groups;
- Kafka lag is visible in observability dashboards.

Costs:

- Kafka is operationally heavier;
- local MVP needs a lightweight substitute;
- event contracts must be maintained.

