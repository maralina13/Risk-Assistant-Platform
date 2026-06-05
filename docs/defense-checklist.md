# Defense checklist

Короткий порядок демонстрации, если на защиту есть 5-7 минут.

## 1. Открыть документы

1. `README.md` - карта проекта и live status.
2. `docs/submission-handoff.md` - короткая карта сдачи.
3. `docs/criteria-matrix.md` - соответствие критериям преподавателя.
4. `docs/live-validation-report.md` - фактические результаты live-проверок.
5. `docs/high-level-scope.md` - ТЗ, User Stories, Use Cases, NFR.
6. `docs/c4-and-sequence.md` - C4 L1-L3 и sequence diagram.

## 2. Проверить проект без кластера

```bash
python3 scripts/check_submission.py
.venv/bin/python -m pytest -q
```

Ожидаемо:

```text
Result: ready for review
10 passed
```

## 3. Показать Kubernetes и GitOps

```bash
kubectl get nodes
kubectl -n argocd get applications.argoproj.io
```

Или одной командой:

```bash
scripts/defense_smoke.sh
```

Ожидаемо:

```text
risk-assistant       Ready
risk-assistant-m02   Ready

risk-assistant-root   Synced   Healthy
risk-assistant        Synced   Healthy
kafka                 Synced   Healthy
platform-infra        Synced   Healthy
observability         Synced   Healthy
```

## 4. Показать микросервисы и CI image

```bash
kubectl -n risk-assistant get deploy api-gateway project-intake-service \
  risk-analysis-service report-service audit-service notification-service \
  -o 'custom-columns=NAME:.metadata.name,READY:.status.readyReplicas,IMAGE:.spec.template.spec.containers[0].image'
```

Ожидаемо: 6 микросервисов используют `localhost:5000/risk-assistant:ci-final-demo`.

## 5. Показать API Gateway

```bash
kubectl -n risk-assistant port-forward svc/api-gateway 8080:8088
curl http://localhost:8080/routes
```

## 6. Показать E2E сценарий

```bash
curl -X POST http://localhost:8080/projects/analyze \
  -H 'Content-Type: application/json' \
  -d '{"project_title":"Defense E2E Allergy App","project_description":"Команда из двух человек хочет сделать мобильное приложение с картой кафе для людей с аллергией, без глютена и без лактозы. Начать планируют с Турции и потом расширяться на другие страны. Есть полгода, важна модерация данных и надежность рекомендаций."}'
```

Потом открыть отчет:

```bash
curl http://localhost:8080/reports/<task_id>
```

Что сказать: запрос прошел через API Gateway, Project Intake опубликовал `ProjectSubmitted` в Kafka,
Risk Analysis построил отчет, Report Service вернул матрицу рисков.

## 7. Показать Observability

```bash
kubectl -n risk-assistant get servicemonitor
kubectl -n observability get prometheusrule risk-assistant-alerts
kubectl -n observability get configmap risk-assistant-grafana-dashboard
```

Prometheus:

```bash
kubectl -n observability port-forward svc/monitoring-kube-prometheus-prometheus 19090:9090
curl 'http://localhost:19090/api/v1/query?query=sum(risk_assistant_service_up)'
```

Ожидаемо: значение `10`.

## 8. Показать CI/CD

```bash
IMAGE_TAG=ci-final-demo scripts/local_ci_pipeline.sh
```

Что сказать: pipeline запускает tests, build image, обновляет GitOps source, пушит в локальный Git daemon,
ArgoCD синхронизирует приложение и проверяется rollout.

## 9. Показать Load / Circuit Breaker

```bash
locust -f tests/load/locustfile.py --host http://localhost:8080 \
  --headless --users 25 --spawn-rate 5 --run-time 45s --only-summary
```

Для отказа:

```bash
DOWN_SECONDS=20 scripts/demo_circuit_breaker.sh
```

Что сказать: при отказе `report-service` появляются временные ошибки на маршруте отчетов,
после восстановления deployment возвращается в `2/2 Running`, а Grafana/Prometheus видят метрики.
