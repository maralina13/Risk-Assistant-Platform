from __future__ import annotations

import os
from uuid import uuid4

from services.shared.events import project_submitted
from services.shared.http_client import request_json
from services.shared.http_service import JsonHandler, run_service
from services.shared.storage import append_event, get_task, save_task, update_task


class ProjectIntakeHandler(JsonHandler):
    service_name = "project-intake-service"
    risk_analysis_url = os.environ.get("RISK_ANALYSIS_URL", "http://localhost:8092")
    auto_process = os.environ.get("AUTO_PROCESS", "false").lower() == "true"

    def do_GET(self) -> None:
        if self.path == "/example-event":
            task_id = str(uuid4())
            event = project_submitted(task_id, "Короткое описание учебного проекта", "Demo project")
            self.send_json(200, event.to_dict())
            return
        if self.path.startswith("/tasks/") and self.path.endswith("/status"):
            task_id = self.path.split("/")[2]
            task = get_task(task_id)
            if task is None:
                self.send_json(404, {"error": "task_not_found", "task_id": task_id})
                return
            self.send_json(200, task)
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/projects/analyze":
            super().do_POST()
            return

        try:
            body = self.read_json()
        except ValueError:
            self.send_json(400, {"error": "invalid_json"})
            return

        project_description = str(body.get("project_description", "")).strip()
        project_title = str(body.get("project_title", "Untitled project")).strip()
        if len(project_description) < 30:
            self.send_json(400, {"error": "project_description_too_short"})
            return

        task_id = str(uuid4())
        task = {
            "task_id": task_id,
            "project_title": project_title,
            "project_description": project_description,
            "status": "pending",
        }
        save_task(task_id, task)
        event = project_submitted(task_id, project_description, project_title)
        published_to_kafka = append_event(event.to_dict())

        process_result = None
        if self.auto_process:
            update_task(task_id, status="running")
            _, process_result = request_json(
                "POST",
                f"{self.risk_analysis_url}/internal/process-task",
                {
                    "task_id": task_id,
                    "project_title": project_title,
                    "project_description": project_description,
                },
            )
            task = get_task(task_id) or task

        self.send_json(
            202,
            {
                "task_id": task_id,
                "status": task["status"],
                "published_event": event.to_dict(),
                "published_to_kafka": published_to_kafka,
                "event_bus": "kafka_redpanda",
                "processing": process_result,
            },
        )


if __name__ == "__main__":
    run_service(ProjectIntakeHandler, 8091)
