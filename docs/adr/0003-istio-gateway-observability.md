# ADR-0003: Istio, HAProxy ingress and Grafana observability

## Status

Accepted.

## Context

The platform must show routing, load balancing, rate limiting, circuit breaker, retry policies, observability and alerting. These concerns should be visible at infrastructure level, not hidden only in application code.

## Decision

Use:

- HAProxy Ingress Controller for incoming HTTP traffic.
- Keepalived for a virtual IP in a local bare-metal-like lab.
- API Gateway for business routing.
- Valkey-backed application rate limiting plus Envoy local rate limit as gateway-level example.
- Istio for service mesh, mTLS, retry, circuit breaker and outlier detection.
- Prometheus, Loki, Tempo, OpenTelemetry Collector, Grafana and Alertmanager for observability.

## Alternatives

- Linkerd instead of Istio: simpler, but fewer explicit traffic-management examples for the assignment.
- Nginx Ingress only: enough for basic ingress, weaker demonstration of mesh-level retries/outlier detection.
- ELK instead of Loki: powerful, but heavy for local Kubernetes.
- VictoriaMetrics/VictoriaLogs: strong production option, but Prometheus/Loki/Tempo is simpler for a teaching stand.

## Consequences

Benefits:

- clear separation between ingress, API routing and service mesh;
- circuit breaker behavior can be validated during Locust tests;
- Grafana dashboards can show latency, 5xx, 429 and Kafka lag;
- stack maps directly to assignment criteria.

Costs:

- more manifests to maintain;
- Istio has a steeper learning curve;
- Keepalived is mostly illustrative in local environments.

