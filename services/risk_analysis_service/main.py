from __future__ import annotations

import threading
import time
from typing import Any

from services.risk_analysis_service.agent_workflow import run_multi_agent_analysis
from services.shared.events import report_generated, risk_analysis_completed, risk_analysis_failed, risk_analysis_started
from services.shared.http_service import JsonHandler, run_service
from services.shared.infrastructure import consume_kafka_events
from services.shared.storage import append_event, get_task, save_report, update_task


def process_task(task_id: str, project_title: str, project_description: str) -> dict[str, Any]:
    print(f"processing task from event: task_id={task_id}", flush=True)
    update_task(task_id, status="running")
    started = risk_analysis_started(task_id, "internal_multi_agent_workflow")
    started_published = append_event(started.to_dict())

    analysis_state = run_multi_agent_analysis(project_title, project_description)
    report = analysis_state["report"]
    report_path = save_report(task_id, report)
    risk_count = len(analysis_state["risks"])
    completed = risk_analysis_completed(task_id, f"report-{task_id}", risk_count)
    generated = report_generated(task_id, str(report_path))
    completed_published = append_event(completed.to_dict())
    generated_published = append_event(generated.to_dict())
    update_task(task_id, status="completed", report_id=f"report-{task_id}", risk_count=risk_count)

    return {
        "task_id": task_id,
        "status": "completed",
        "events": [started.to_dict(), completed.to_dict(), generated.to_dict()],
        "published_to_kafka": {
            "RiskAnalysisStarted": started_published,
            "RiskAnalysisCompleted": completed_published,
            "ReportGenerated": generated_published,
        },
    }


def handle_project_submitted_event(event: dict[str, Any]) -> None:
    print(f"received kafka event: {event.get('event_type')} id={event.get('event_id')}", flush=True)
    payload = event.get("payload", {})
    task_id = str(payload.get("task_id", "")).strip()
    if not task_id:
        print("skip event without task_id", flush=True)
        return

    task = get_task(task_id)
    if task and task.get("status") == "completed":
        print(f"skip completed task: {task_id}", flush=True)
        return

    project_title = str((task or {}).get("project_title", payload.get("project_title", "Untitled project")))
    project_description = str((task or {}).get("project_description", payload.get("project_description", "")))
    if len(project_description.strip()) < 30:
        print(f"skip task with short description: {task_id}", flush=True)
        return

    process_task(task_id, project_title, project_description)


def kafka_worker() -> None:
    while True:
        try:
            consumer = consume_kafka_events(["project-events"], group_id="risk-analysis-service")
            for message in consumer:
                try:
                    event = message.value
                    if event.get("event_type") == "ProjectSubmitted":
                        handle_project_submitted_event(event)
                except Exception as error:
                    print(f"kafka message handling failed: {error}", flush=True)
            consumer.close()
        except Exception as error:
            print(f"kafka worker reconnect after error: {error}", flush=True)
            time.sleep(2)


def start_kafka_worker() -> None:
    thread = threading.Thread(target=kafka_worker, name="risk-analysis-kafka-worker", daemon=True)
    thread.start()


class RiskAnalysisHandler(JsonHandler):
    service_name = "risk-analysis-service"

    def do_GET(self) -> None:
        if self.path == "/responsibility":
            self.send_json(
                200,
                {
                    "service": self.service_name,
                    "responsibility": "runs an internal multi-agent risk workflow and prepares markdown reports",
                    "subscribes": ["ProjectSubmitted from Kafka topic project-events"],
                    "workflow": [
                        "Requirement Analyst Agent",
                        "Risk Analyst Agent",
                        "Mitigation Planner Agent",
                        "Critic / Validator Agent",
                        "Report Writer Agent",
                    ],
                    "publishes": ["RiskAnalysisStarted", "RiskAnalysisCompleted", "RiskAnalysisFailed"],
                },
            )
            return
        if self.path == "/example-event":
            event = risk_analysis_completed("task-demo", "report-demo", 5)
            self.send_json(200, event.to_dict())
            return
        if self.path == "/example-started":
            event = risk_analysis_started("task-demo", "demo")
            self.send_json(200, event.to_dict())
            return
        if self.path == "/example-failed":
            event = risk_analysis_failed("task-demo", "ANALYSIS_TIMEOUT", "analysis timeout", True)
            self.send_json(200, event.to_dict())
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/internal/process-task":
            super().do_POST()
            return

        try:
            body = self.read_json()
        except ValueError:
            self.send_json(400, {"error": "invalid_json"})
            return

        task_id = str(body.get("task_id", "")).strip()
        project_title = str(body.get("project_title", "Untitled project")).strip()
        project_description = str(body.get("project_description", "")).strip()
        if not task_id:
            self.send_json(400, {"error": "task_id_required"})
            return

        self.send_json(200, process_task(task_id, project_title, project_description))


if __name__ == "__main__":
    start_kafka_worker()
    run_service(RiskAnalysisHandler, 8092)
