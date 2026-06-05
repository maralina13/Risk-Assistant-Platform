# Real usage audit

Дата проверки: 2026-05-28.

Этот файл отвечает на главный риск защиты: компоненты платформы не просто лежат в репозитории, а
используются в live-сценарии проекта.

| Требование | Как используется в проекте | Live-доказательство |
| --- | --- | --- |
| Kubernetes cluster | Все 6 микросервисов, Kafka-compatible broker, observability, gateway и CI registry запущены в локальном кластере `risk-assistant`. | `kubectl --context risk-assistant get nodes` показывает control-plane и worker `Ready`. |
| Cilium CNI | CNI поднят в `kube-system`; сетевые политики описаны для namespace `risk-assistant`. | `kubectl --context risk-assistant -n kube-system get pods -l k8s-app=cilium`. |
| Cluster Autoscaler | Deployment работает в `kube-system` с KWOK provider config и node group `risk-assistant-local-workers`; demo workload создает pending pods с высоким CPU request, чтобы показать реакцию autoscaler на scheduling pressure. | `cluster-autoscaler` pod `1/1 Running`; `scripts/demo_cluster_autoscaler.sh`; logs показывают `4 unschedulable pods left` и `No expansion options` для локального Minikube. |
| Terraform | Terraform описывает базовые namespaces, service accounts и bootstrap secrets как IaC-слой. | `infra/terraform/main.tf`; live namespaces совпадают с Terraform-моделью. |
| ArgoCD App of Apps | Root application синхронизирует `platform-infra`, `kafka`, `observability`, `risk-assistant`. | ArgoCD applications: `Synced / Healthy`. |
| Ansible + Strimzi Kafka | Ansible role устанавливает Strimzi Kafka как целевой вариант; для live Minikube используется Redpanda как Kafka API-compatible broker. | `infra/ansible/roles/strimzi-kafka/`; live pod `risk-kafka-0 Running`. |
| Istio service mesh | Микросервисы запускаются с Istio sidecar/init containers; DestinationRule задает retry/outlier detection/circuit breaker. | `kubectl -n risk-assistant get pod ... -o jsonpath` показывает `istio-init` и `istio-proxy`; circuit breaker demo проходит. |
| HAProxy Ingress | Внешний маршрут `risk-assistant.local` ведет через HAProxy Ingress к `api-gateway`. | `scripts/demo_ingress_e2e.sh` выполняет `/routes`, `POST /projects/analyze`, `GET /reports/{task_id}` через HAProxy. |
| Keepalived | DaemonSet запущен на двух нодах как слой HA для точки входа. | `keepalived` pods `1/1 Running` на control-plane и worker. |
| Rate limiting | API Gateway ограничивает поток запросов; load test подтверждает ответы `429 Too Many Requests` при перегрузе. | `docs/live-validation-report.md`, раздел Load test. |
| Observability | Prometheus scrape'ит сервисы, Grafana dashboard и alert rules подключены; Loki принимает и отдаёт demo log; OTel Collector принимает OTLP trace и отправляет его в Tempo. | Prometheus targets для `risk-assistant`: `10/10 healthy`; `scripts/validate_observability_deep.sh` проверяет Loki push/query и Tempo trace query. |
| GitLab Runner + Local CI/CD | GitLab Runner установлен Helm chart'ом в namespace `cicd`, зарегистрирован в GitLab project runner и использует Kubernetes executor; live Kaniko job собирает image внутри Kubernetes и push'ит его в in-cluster registry. | `gitlab-runner` pod `1/1 Running`; logs: `Runner registered successfully`; `scripts/live_kaniko_pipeline.sh` завершился с registry tags `latest`, `ci-kaniko-live`. |
| Helm charts | Один chart разворачивает 6 микросервисов с Kafka, Valkey/cache и data-store env settings. | ArgoCD application `risk-assistant` `Synced / Healthy`; deployments используют Helm labels. |
| Locust | Нагрузочный сценарий гонит запросы через API Gateway в микросервисы и инициирует Kafka event flow. | `tests/load/locustfile.py`; live run: 859 requests, 0 failures. |

## Честные ограничения локального стенда

- Minikube не создает новые физические/виртуальные worker nodes через cloud API, поэтому Cluster
  Autoscaler показан как рабочий локальный контроллер с KWOK provider config. Для реального
  node provisioning нужен cloud provider, Cluster API или отдельный k3s/k0s/Talos setup.
- Keepalived в Docker-based Minikube запускается как DaemonSet, но production-like VIP с доступом
  напрямую с macOS host требует контроля L2-сети или bare-metal окружения.
- GitLab Runner values и GitLab pipeline описаны, но полноценная регистрация runner требует URL и
  registration token от GitLab. В live-контуре роль build job выполняет Kubernetes Kaniko Job.
