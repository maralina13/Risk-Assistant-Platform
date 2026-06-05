from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "requirements.txt",
    "requirements-dev.txt",
    "docs/high-level-scope.md",
    "docs/c4-and-sequence.md",
    "docs/platform-implementation.md",
    "docs/criteria-matrix.md",
    "docs/real-usage-audit.md",
    "docs/defense-notes.md",
    "docs/defense-checklist.md",
    "docs/submission-handoff.md",
    "docs/teacher-qa.md",
    "docs/demo-scenario.md",
    "docs/live-validation-report.md",
    "docs/adr/0001-event-driven-kafka.md",
    "docs/adr/0002-polyglot-persistence.md",
    "docs/adr/0003-istio-gateway-observability.md",
    "docs/runbooks/local-cluster.md",
    "docs/runbooks/deploy-and-validate.md",
    "contracts/openapi.yaml",
    "contracts/asyncapi.yaml",
    "contracts/events/event.schema.json",
    "infra/kafka/topics.json",
    "infra/kubernetes/base/namespaces.yaml",
    "infra/kubernetes/cluster/cilium-network-policies.yaml",
    "infra/kubernetes/cluster/cluster-autoscaler.yaml",
    "infra/kubernetes/cluster/autoscaler-demo-workload.yaml",
    "infra/kubernetes/gateway/haproxy-ingress.yaml",
    "infra/kubernetes/gateway/keepalived.yaml",
    "infra/kubernetes/gateway/rate-limit.yaml",
    "infra/kubernetes/ci/local-registry.yaml",
    "infra/kubernetes/kafka/kafka-cluster.yaml",
    "infra/kubernetes/kafka/redpanda-local.yaml",
    "infra/kubernetes/mesh/istio-policies.yaml",
    "infra/terraform/main.tf",
    "infra/argocd/root-app.yaml",
    "infra/ansible/deploy-kafka.yml",
    "infra/ansible/roles/strimzi-kafka/tasks/main.yml",
    "infra/helm/risk-assistant/Chart.yaml",
    "infra/helm/risk-assistant/values.yaml",
    "infra/helm/risk-assistant/templates/pdb.yaml",
    "infra/helm/risk-assistant/templates/networkpolicy.yaml",
    "infra/helm/risk-assistant/templates/servicemonitor.yaml",
    "infra/observability/dashboards/risk-assistant-dashboard.json",
    "infra/observability/loki-local.yaml",
    "infra/observability/prometheus-rules.yaml",
    "infra/observability/servicemonitor-kafka.yaml",
    "infra/observability/tempo-local.yaml",
    "infra/ci/gitlab-ci.yml",
    "infra/ci/gitlab-runner-values.yaml",
    "infra/ci/kaniko-build-job.yaml",
    "infra/ci/kaniko-live-job.yaml",
    "scripts/bootstrap_local_cluster.sh",
    "scripts/deploy_platform.sh",
    "scripts/validate_live_cluster.sh",
    "scripts/validate_observability_deep.sh",
    "scripts/defense_smoke.sh",
    "scripts/demo_e2e.sh",
    "scripts/demo_circuit_breaker.sh",
    "scripts/demo_cluster_autoscaler.sh",
    "scripts/demo_ingress_e2e.sh",
    "scripts/local_ci_pipeline.sh",
    "scripts/live_kaniko_pipeline.sh",
    "tests/load/locustfile.py",
]

KEY_TERMS = {
    "docs/high-level-scope.md": [
        "ГОСТ",
        "User Stories",
        "Use Cases",
        "NFR",
        "Kafka",
        "RabbitMQ",
        "NATS",
        "Valkey",
        "Rate Limiter",
    ],
    "docs/c4-and-sequence.md": [
        "C4 L1",
        "C4 L2",
        "C4 L3",
        "Sequence Diagram",
        "mermaid",
    ],
    "docs/platform-implementation.md": [
        "Cilium",
        "Cluster Autoscaler",
        "Terraform",
        "ArgoCD",
        "Strimzi",
        "Istio",
        "HAProxy",
        "Keepalived",
        "Locust",
    ],
    "docs/live-validation-report.md": [
        "Synced",
        "Healthy",
        "ci-final-demo",
        "ci-kaniko-live",
        "risk_assistant_service_up",
        "Locust",
        "Circuit breaker",
        "Loki",
        "Tempo",
    ],
    "docs/real-usage-audit.md": [
        "Real usage",
        "Cluster Autoscaler",
        "KWOK",
        "HAProxy Ingress",
        "Kaniko",
        "in-cluster registry",
    ],
}


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def ok(message: str) -> None:
    print(f"[ OK ] {message}")


def check_required_files() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    if missing:
        fail("Missing required files:\n" + "\n".join(f"  - {path}" for path in missing))
    ok(f"Required files present: {len(REQUIRED_FILES)}")


def check_json_files() -> None:
    json_files = sorted(ROOT.glob("contracts/events/*.json"))
    json_files += [
        ROOT / "infra/kafka/topics.json",
        ROOT / "infra/observability/dashboards/risk-assistant-dashboard.json",
    ]
    for path in json_files:
        with path.open(encoding="utf-8") as file:
            json.load(file)
    ok(f"JSON files are valid: {len(json_files)}")


def check_python_files() -> None:
    python_files = sorted((ROOT / "services").glob("**/*.py"))
    python_files += sorted((ROOT / "tests").glob("**/*.py"))
    python_files.append(ROOT / "scripts/check_submission.py")
    for path in python_files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    ok(f"Python files compile: {len(python_files)}")


def check_docs_keywords() -> None:
    for relative_path, terms in KEY_TERMS.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        missing_terms = [term for term in terms if term not in text]
        if missing_terms:
            fail(f"{relative_path} misses terms: {', '.join(missing_terms)}")
    ok("Documentation contains required architecture terms")


def check_service_count() -> None:
    service_dirs = [
        path
        for path in (ROOT / "services").iterdir()
        if path.is_dir() and (path.name.endswith("_service") or path.name == "api_gateway")
    ]
    if len(service_dirs) < 6:
        fail(f"Expected at least 6 deployed microservices/components, found {len(service_dirs)}")
    ok(f"Microservice directories found: {len(service_dirs)}")


def check_shell_scripts() -> None:
    scripts = sorted((ROOT / "scripts").glob("*.sh"))
    for path in scripts:
        if not path.stat().st_mode & 0o111:
            fail(f"Shell script is not executable: {path.relative_to(ROOT)}")
    if shutil.which("bash"):
        subprocess.run(["bash", "-n", *map(str, scripts)], check=True)
        ok(f"Executable shell scripts with valid syntax found: {len(scripts)}")
        return
    ok(f"Executable shell scripts found: {len(scripts)}")


def main() -> int:
    print("Submission self-check")
    print(f"Root: {ROOT}")
    check_required_files()
    check_json_files()
    check_python_files()
    check_docs_keywords()
    check_service_count()
    check_shell_scripts()
    print("Result: ready for review")
    return 0


if __name__ == "__main__":
    sys.exit(main())
