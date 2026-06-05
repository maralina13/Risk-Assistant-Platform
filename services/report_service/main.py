from __future__ import annotations

from services.shared.events import report_generated
from services.shared.http_service import JsonHandler, run_service
from services.shared.storage import read_report


class ReportHandler(JsonHandler):
    service_name = "report-service"

    def do_GET(self) -> None:
        if self.path == "/example-event":
            event = report_generated("task-demo", "runtime/reports/task-demo.md")
            self.send_json(200, event.to_dict())
            return
        if self.path.startswith("/reports/"):
            task_id = self.path.split("/")[2]
            report = read_report(task_id)
            if report is None:
                self.send_json(404, {"error": "report_not_found", "task_id": task_id})
                return
            self.send_json(
                200,
                {
                    "task_id": task_id,
                    "format": "markdown",
                    "report": report,
                },
            )
            return
        super().do_GET()


if __name__ == "__main__":
    run_service(ReportHandler, 8093)
