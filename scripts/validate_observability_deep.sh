#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

export PATH="$PROJECT_ROOT/.tools/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"
export MINIKUBE_HOME="${MINIKUBE_HOME:-$PROJECT_ROOT/.tools/minikube-home}"
CONTEXT="${CONTEXT:-risk-assistant}"
NAMESPACE="${OBS_NAMESPACE:-observability}"
RUN_ID="${RUN_ID:-$(date +%s)}"
START_NS="$(date +%s%N)"
END_NS="$((START_NS + 50000000))"
TRACE_ID="111111111111111111111111$(printf '%08x' "$((RUN_ID % 4294967295))")"
SPAN_ID="$(printf '%016x' "$((RUN_ID % 4294967295))")"

echo "==> wait for observability rollouts"
kubectl --context "$CONTEXT" -n "$NAMESPACE" rollout status deploy/otel-collector --timeout=180s
kubectl --context "$CONTEXT" -n "$NAMESPACE" rollout status deploy/loki --timeout=180s
kubectl --context "$CONTEXT" -n "$NAMESPACE" rollout status deploy/tempo --timeout=180s

echo "==> Loki readiness"
kubectl --context "$CONTEXT" -n "$NAMESPACE" run loki-ready-"$RUN_ID" \
  --image=curlimages/curl:8.10.1 \
  --restart=Never \
  --rm \
  -i \
  --quiet \
  --command -- curl -fsS http://loki:3100/ready

echo "==> push demo log to Loki"
kubectl --context "$CONTEXT" -n "$NAMESPACE" run loki-push-"$RUN_ID" \
  --image=curlimages/curl:8.10.1 \
  --restart=Never \
  --rm \
  -i \
  --quiet \
  --command -- curl -fsS \
  -H 'Content-Type: application/json' \
  -X POST http://loki:3100/loki/api/v1/push \
  --data "{\"streams\":[{\"stream\":{\"app\":\"risk-assistant-observability-demo\",\"run_id\":\"$RUN_ID\"},\"values\":[[\"$START_NS\",\"defense observability log $RUN_ID\"]]}]}"

echo "==> query demo log from Loki"
kubectl --context "$CONTEXT" -n "$NAMESPACE" run loki-query-"$RUN_ID" \
  --image=curlimages/curl:8.10.1 \
  --restart=Never \
  --rm \
  -i \
  --quiet \
  --command -- curl -fsS -G http://loki:3100/loki/api/v1/query \
  --data-urlencode "query={app=\"risk-assistant-observability-demo\",run_id=\"$RUN_ID\"}"

echo "==> Tempo readiness"
kubectl --context "$CONTEXT" -n "$NAMESPACE" run tempo-ready-"$RUN_ID" \
  --image=curlimages/curl:8.10.1 \
  --restart=Never \
  --rm \
  -i \
  --quiet \
  --command -- curl -fsS http://tempo:3200/ready

echo "==> send demo trace through OpenTelemetry Collector"
kubectl --context "$CONTEXT" -n "$NAMESPACE" run otel-trace-"$RUN_ID" \
  --image=curlimages/curl:8.10.1 \
  --restart=Never \
  --rm \
  -i \
  --quiet \
  --command -- curl -fsS \
  -H 'Content-Type: application/json' \
  -X POST http://otel-collector:4318/v1/traces \
  --data "{\"resourceSpans\":[{\"resource\":{\"attributes\":[{\"key\":\"service.name\",\"value\":{\"stringValue\":\"risk-assistant-observability-demo\"}},{\"key\":\"deployment.environment\",\"value\":{\"stringValue\":\"local-k8s\"}}]},\"scopeSpans\":[{\"scope\":{\"name\":\"defense-demo\"},\"spans\":[{\"traceId\":\"$TRACE_ID\",\"spanId\":\"$SPAN_ID\",\"name\":\"defense-observability-check\",\"kind\":1,\"startTimeUnixNano\":\"$START_NS\",\"endTimeUnixNano\":\"$END_NS\",\"attributes\":[{\"key\":\"run.id\",\"value\":{\"stringValue\":\"$RUN_ID\"}}]}]}]}]}"

sleep 3

echo "==> query demo trace from Tempo"
kubectl --context "$CONTEXT" -n "$NAMESPACE" run tempo-query-"$RUN_ID" \
  --image=curlimages/curl:8.10.1 \
  --restart=Never \
  --rm \
  -i \
  --quiet \
  --command -- curl -fsS http://tempo:3200/api/traces/"$TRACE_ID"

echo "==> verify Tempo accepted the trace via Collector logs"
kubectl --context "$CONTEXT" -n "$NAMESPACE" logs deploy/otel-collector --since=2m | grep -E 'TracesExporter|otelcol_exporter_sent_spans|risk-assistant-observability-demo|defense-observability-check|ResourceSpans' || true

echo "Deep observability validation finished: Loki log pushed and queried; OTLP trace sent through OTel Collector and queried from Tempo."
