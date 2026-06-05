# Runbook: deploy and validate

## Локальный docker-compose MVP

```bash
docker compose -f docker-compose.architecture.yml up --build
```

Проверка:

```bash
curl http://localhost:8080/routes
python3 scripts/check_submission.py
```

## Kubernetes deploy

Если кластер уже поднят:

```bash
kubectl apply -f infra/kubernetes/kafka/redpanda-local.yaml
scripts/deploy_platform.sh
```

Для проверки через port-forward:

```bash
kubectl -n risk-assistant port-forward svc/api-gateway 8080:8088
scripts/validate_live_cluster.sh
```

## GitOps через ArgoCD

Для live-демо в локальном minikube можно отдать текущий проект в ArgoCD через временный Git daemon:

```bash
git daemon --reuseaddr --base-path=/tmp/risk-assistant-git-base --export-all --informative-errors --verbose
kubectl apply -f infra/argocd/root-app.yaml
kubectl -n argocd get applications.argoproj.io
```

Ожидаемый результат:

```text
risk-assistant-root   Synced   Healthy
risk-assistant        Synced   Healthy
kafka                 Synced   Healthy
platform-infra        Synced   Healthy
observability         Synced   Healthy
```

Если ArgoCD собирает kustomize overlays с относительными ссылками, repo-server должен иметь опцию:

```bash
kubectl -n argocd patch configmap argocd-cm --type merge \
  -p '{"data":{"kustomize.buildOptions":"--load-restrictor LoadRestrictionsNone"}}'
kubectl -n argocd rollout restart deploy/argocd-repo-server
```

## CI/CD

Локальный runner-пайплайн без внешнего GitLab:

```bash
IMAGE_TAG=ci-final-demo scripts/local_ci_pipeline.sh
```

Что делает pipeline:

- запускает `pytest`;
- собирает Docker image;
- загружает image в minikube;
- обновляет GitOps image tag;
- пушит изменение в локальный Git daemon;
- ждёт ArgoCD rollout.

Ожидаемый live-результат:

```text
10 passed
Local CI pipeline finished: localhost:5000/risk-assistant:ci-final-demo
```

Проверка image:

```bash
kubectl -n risk-assistant get deploy api-gateway \
  -o jsonpath="{.spec.template.spec.containers[0].image}"
```

## Observability

Установка Prometheus, Grafana и Alertmanager:

```bash
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n observability \
  -f infra/observability/kube-prometheus-values.yaml
```

Проверки:

```bash
kubectl -n observability get pods
kubectl -n risk-assistant get servicemonitor
kubectl -n observability get prometheusrule risk-assistant-alerts
```

Проверка Prometheus scrape:

```bash
kubectl -n observability port-forward svc/monitoring-kube-prometheus-prometheus 19090:9090
curl 'http://localhost:19090/api/v1/query?query=sum(risk_assistant_service_up)'
```

Ожидаемый live-результат:

```text
risk-assistant targets: 10
healthy targets: 10
sum(risk_assistant_service_up): 10
```

Grafana:

```bash
kubectl -n observability port-forward svc/monitoring-grafana 3000:80
kubectl -n observability get secret monitoring-grafana \
  -o jsonpath="{.data.admin-password}" | base64 -d
```

Dashboard `Risk Assistant Platform` загружается через ConfigMap `risk-assistant-grafana-dashboard`
с label `grafana_dashboard=1`.

Для live-демо ArgoCD передаёт Helm-параметр `networkPolicy.enabled=false`, чтобы Prometheus мог
scrape'ить все микросервисы. Сам шаблон NetworkPolicy остаётся в Helm chart и может быть включён
для отдельной проверки сетевой изоляции.

## Locust

```bash
locust -f tests/load/locustfile.py --host http://localhost:8080 \
  --headless --users 25 --spawn-rate 5 --run-time 45s --only-summary
```

Ожидаемый live-результат после настройки expected statuses:

```text
859 requests, 0 failures, ~19 req/s, median latency ~9 ms
```

## Circuit Breaker demo

Во время нагрузки:

```bash
locust -f tests/load/locustfile.py --host http://localhost:8080 \
  --headless --users 15 --spawn-rate 5 --run-time 70s --only-summary
scripts/demo_circuit_breaker.sh
```

Ожидаемый live-результат:

```text
report-service scaled to 0
GET /reports/{missing}: temporary failures during outage
report-service rollout successfully restored to 2/2
```

В Grafana проверить:

- `istio_requests_total` с 5xx/503;
- P95 latency;
- rate limiter 429;
- Kafka consumer lag;
- восстановление после возврата `report-service`.
