# Матрица соответствия критериям преподавателя

## High-level Scope, часть 1

| Требование | Статус | Где смотреть |
| --- | --- | --- |
| 1. ТЗ по ГОСТ 19/34, ключевые пункты | Готово | `docs/high-level-scope.md`, раздел 1 |
| 2. User Story + Use Cases + NFR | Готово | `docs/high-level-scope.md`, разделы 2-4 |
| 3. C4 L1-3 + Sequence Diagram | Готово | `docs/c4-and-sequence.md` |
| 4. Микросервисы 3+ и распределение по команде | Готово | `docs/high-level-scope.md`, раздел 5; `services/` |
| 5. Kafka, сравнение RabbitMQ vs NATS, выбор Kafka, EDA | Готово | `docs/high-level-scope.md`, раздел 6 |
| 6. Данные: RDBMS + NoSQL/cold storage | Готово | `docs/high-level-scope.md`, раздел 7; `infra/postgres/schema.sql` |
| 7. Redis-like cache | Готово | `services/shared/infrastructure.py`, `docker-compose.architecture.yml`, Helm values |
| 8. Routing layer: router + balancer + rate limiter | Готово | `services/api_gateway/main.py`, `infra/nginx/nginx.conf`, `infra/kubernetes/gateway/` |

## Часть 2. Локальная инфраструктура и Kubernetes

| Требование | Статус | Где смотреть |
| --- | --- | --- |
| 1.1 Kubernetes + Cilium CNI | Поднято live | `docs/live-validation-report.md`, `docs/real-usage-audit.md`, `infra/kubernetes/cluster/cilium-network-policies.yaml` |
| 1.2 Karpenter или Cluster Autoscaler | Cluster Autoscaler Running с KWOK provider config и demo-нагрузкой | `infra/kubernetes/cluster/cluster-autoscaler.yaml`, `infra/kubernetes/cluster/autoscaler-demo-workload.yaml`, `scripts/demo_cluster_autoscaler.sh`, `docs/real-usage-audit.md` |
| Live bootstrap локального кластера | Готово | `scripts/bootstrap_local_cluster.sh`, `docs/runbooks/local-cluster.md` |

## Часть 3. IaC + GitOps

| Требование | Статус | Где смотреть |
| --- | --- | --- |
| 2.1 Terraform namespaces, service accounts, secrets | Готово | `infra/terraform/main.tf` |
| 2.2 ArgoCD App of Apps | Готово | `infra/argocd/root-app.yaml`, `infra/argocd/apps/` |
| 2.3 Ansible Role для Kafka/Strimzi | Готово | `infra/ansible/roles/strimzi-kafka/` |

## Часть 4. Ядро системы и трафик

| Требование | Статус | Где смотреть |
| --- | --- | --- |
| 3.1 Istio/Linkerd, Circuit Breaker, Outlier Detection, retry | Istio | `infra/kubernetes/mesh/istio-policies.yaml` |
| 3.2 Ingress Controller + HAProxy/Keepalived | Готово и проверено через HAProxy E2E | `infra/kubernetes/gateway/haproxy-ingress.yaml`, `infra/kubernetes/gateway/keepalived.yaml`, `scripts/demo_ingress_e2e.sh` |
| 3.3 Rate Limiting на Ingress/Gateway API | Готово и проверено нагрузкой | `infra/kubernetes/gateway/rate-limit.yaml`, `services/api_gateway/main.py`, `docs/live-validation-report.md` |
| PDB/NetworkPolicy/securityContext | Готово | `infra/helm/risk-assistant/templates/pdb.yaml`, `networkpolicy.yaml`, `deployments.yaml` |

## Часть 5. Observability

| Требование | Статус | Где смотреть |
| --- | --- | --- |
| Рассмотреть варианты логов/метрик/трейсов | Готово | `docs/platform-implementation.md`, часть 4 |
| Логи | Loki выбран, VictoriaLogs/ELK/SigNoz сравнены; Loki live push/query проверен | `infra/observability/loki-values.yaml`, `infra/observability/loki-local.yaml`, `scripts/validate_observability_deep.sh` |
| Метрики | Prometheus выбран | `infra/observability/kube-prometheus-values.yaml` |
| Трейсы | Tempo + OpenTelemetry Collector; OTLP trace live отправлен и queried из Tempo | `infra/observability/tempo-values.yaml`, `infra/observability/tempo-local.yaml`, `infra/observability/otel-collector.yaml`, `scripts/validate_observability_deep.sh` |
| Grafana dashboards | Готово | `infra/observability/dashboards/risk-assistant-dashboard.json` |
| Alerting | Готово | `infra/observability/prometheus-rules.yaml` |
| ServiceMonitor/PodMonitor | Готово | `infra/helm/risk-assistant/templates/servicemonitor.yaml`, `infra/observability/servicemonitor-kafka.yaml` |

## Часть 6. CI/CD и окружение разработки

| Требование | Статус | Где смотреть |
| --- | --- | --- |
| 5.1 Локальный GitLab Runner/GitHub Actions Self-Hosted | Готово live: GitLab Runner установлен в K8s, зарегистрирован в GitLab и `1/1 Running` | `infra/ci/gitlab-runner-values.yaml`, `kubectl -n cicd get pods -l app=gitlab-runner`, logs: `Runner registered successfully` |
| 5.2 Build Kaniko, Push registry, Update Helm, ArgoCD Sync | Готово: local CI + live Kaniko push в in-cluster registry | `infra/ci/gitlab-ci.yml`, `infra/ci/kaniko-build-job.yaml`, `infra/ci/kaniko-live-job.yaml`, `scripts/local_ci_pipeline.sh`, `scripts/live_kaniko_pipeline.sh` |
| 5.3 Helm charts для 3+ микросервисов | Готово, 6 сервисов | `infra/helm/risk-assistant/` |

## Часть 7. Тестирование и валидация платформы

| Требование | Статус | Где смотреть |
| --- | --- | --- |
| 6.1 Locust load testing | Готово | `tests/load/locustfile.py` |
| 6.2 Проверка Circuit Breaker | Проверено live | `scripts/demo_circuit_breaker.sh`, `docs/runbooks/deploy-and-validate.md` |
| 6.3 Валидация Grafana dashboards | Проверено live: Prometheus targets 10/10 healthy | `docs/platform-implementation.md`, часть 6.3; `infra/observability/dashboards/` |
| Live validation scripts | Готово | `scripts/validate_live_cluster.sh`, `scripts/demo_circuit_breaker.sh`, `docs/runbooks/deploy-and-validate.md` |

## Что можно сказать на защите

Проект демонстрирует не только код микросервисов, но и платформенную обвязку: события, контракты, GitOps, IaC, Helm, service mesh, gateway, rate limiting, observability, CI/CD и нагрузочную проверку. Локальный MVP можно запустить через docker compose, а Kubernetes-версия поднята как production-like контур; что именно реально используется, сведено в `docs/real-usage-audit.md`.
