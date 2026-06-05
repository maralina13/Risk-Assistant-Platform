PYTHON ?= python3
HELM ?= helm
LOCUST ?= locust

.PHONY: architecture-check compose-architecture docs-check helm-template load-test submission-check

architecture-check:
	$(PYTHON) -m pytest tests/test_service_events.py
	$(PYTHON) -m compileall -q services

compose-architecture:
	bash scripts/compose_architecture.sh

docs-check:
	$(PYTHON) -m json.tool infra/observability/dashboards/risk-assistant-dashboard.json >/dev/null
	$(PYTHON) -m compileall -q services tests/load

submission-check:
	$(PYTHON) scripts/check_submission.py

helm-template:
	$(HELM) template risk-assistant infra/helm/risk-assistant --namespace risk-assistant

load-test:
	$(LOCUST) -f tests/load/locustfile.py --host http://localhost:8080
