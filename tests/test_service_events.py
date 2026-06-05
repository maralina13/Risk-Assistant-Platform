import json
from pathlib import Path

from services.risk_analysis_service.agent_workflow import run_multi_agent_analysis
from services.shared.events import (
    notification_sent,
    project_submitted,
    report_generated,
    risk_analysis_completed,
    risk_analysis_failed,
    risk_analysis_started,
)


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_project_submitted_event_contract() -> None:
    event = project_submitted("task-1", "Описание проекта")

    data = event.to_dict()

    assert data["event_type"] == "ProjectSubmitted"
    assert data["version"] == "1.0"
    assert data["payload"]["task_id"] == "task-1"
    assert "project_title" in data["payload"]
    assert data["payload"]["status"] == "pending"


def test_risk_analysis_completed_event_contract() -> None:
    event = risk_analysis_completed("task-1", "report-1", 5)

    data = event.to_dict()

    assert data["event_type"] == "RiskAnalysisCompleted"
    assert data["payload"]["task_id"] == "task-1"
    assert data["payload"]["report_id"] == "report-1"
    assert data["payload"]["risk_count"] == 5


def test_risk_analysis_started_event_contract() -> None:
    event = risk_analysis_started("task-1", "demo")

    data = event.to_dict()

    assert data["event_type"] == "RiskAnalysisStarted"
    assert data["payload"]["status"] == "running"
    assert data["payload"]["llm_mode"] == "demo"


def test_risk_analysis_failed_event_contract() -> None:
    event = risk_analysis_failed("task-1", "LLM_TIMEOUT", "timeout", True)

    data = event.to_dict()

    assert data["event_type"] == "RiskAnalysisFailed"
    assert data["payload"]["error_code"] == "LLM_TIMEOUT"
    assert data["payload"]["retryable"] is True


def test_report_generated_event_contract() -> None:
    event = report_generated("task-1", "runtime/reports/task-1.md")

    data = event.to_dict()

    assert data["event_type"] == "ReportGenerated"
    assert data["payload"]["report_path"] == "runtime/reports/task-1.md"


def test_notification_sent_event_contract() -> None:
    event = notification_sent("task-1", "email", "sent")

    data = event.to_dict()

    assert data["event_type"] == "NotificationSent"
    assert data["payload"]["channel"] == "email"
    assert data["payload"]["status"] == "sent"


def test_contract_json_files_are_valid() -> None:
    contract_files = [
        ROOT_DIR / "infra" / "kafka" / "topics.json",
        ROOT_DIR / "contracts" / "events" / "event.schema.json",
        ROOT_DIR / "contracts" / "events" / "project_submitted.schema.json",
        ROOT_DIR / "contracts" / "events" / "risk_analysis_started.schema.json",
        ROOT_DIR / "contracts" / "events" / "risk_analysis_completed.schema.json",
        ROOT_DIR / "contracts" / "events" / "risk_analysis_failed.schema.json",
        ROOT_DIR / "contracts" / "events" / "report_generated.schema.json",
        ROOT_DIR / "contracts" / "events" / "notification_sent.schema.json",
    ]

    for path in contract_files:
        assert path.exists()
        json.loads(path.read_text(encoding="utf-8"))


def test_internal_multi_agent_workflow_builds_contextual_report() -> None:
    state = run_multi_agent_analysis(
        "Приложение для людей с аллергиями",
        (
            "Команда из двух человек хочет сделать мобильное приложение с картой кафе "
            "для людей с аллергией, без глютена и без лактозы. Начать планируют с Турции "
            "и потом расширяться на другие страны. Есть полгода."
        ),
    )

    assert len(state["risks"]) >= 4
    assert state["validation"]["status"] == "approved"
    assert state["revision_count"] >= 1
    assert "Requirement Analyst Agent" in state["report"]
    assert "Матрица рисков" in state["report"]
    assert "аллерг" in state["report"].lower()


def test_append_event_can_record_without_republishing(tmp_path, monkeypatch) -> None:
    from services.shared import storage

    published_events = []
    monkeypatch.setattr(storage, "RUNTIME_DIR", tmp_path)
    monkeypatch.setattr(storage, "TASKS_FILE", tmp_path / "tasks.json")
    monkeypatch.setattr(storage, "EVENTS_FILE", tmp_path / "events.jsonl")
    monkeypatch.setattr(storage, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(storage, "publish_event_to_kafka", lambda event: published_events.append(event) or True)

    event = project_submitted("task-1", "Описание проекта для проверки audit записи").to_dict()
    published = storage.append_event(event, publish=False)

    assert published is False
    assert published_events == []
    assert storage.read_events()[-1]["event_type"] == "ProjectSubmitted"


def test_notification_service_publishes_notification_for_report_event(monkeypatch) -> None:
    from services.notification_service import main as notification_main

    recorded_events = []
    monkeypatch.setattr(notification_main, "append_event", lambda event: recorded_events.append(event) or True)

    notification_main.handle_report_generated_event(report_generated("task-1", "runtime/reports/task-1.md").to_dict())

    assert recorded_events
    assert recorded_events[0]["event_type"] == "NotificationSent"
    assert recorded_events[0]["payload"]["task_id"] == "task-1"
