from __future__ import annotations

import threading
import time
from typing import Any

from services.shared.events import notification_sent
from services.shared.http_service import JsonHandler, run_service
from services.shared.infrastructure import consume_kafka_events
from services.shared.storage import append_event


def handle_report_generated_event(event: dict[str, Any]) -> None:
    if event.get("event_type") != "ReportGenerated":
        return
    task_id = str(event.get("payload", {}).get("task_id", "")).strip()
    if not task_id:
        return
    notification = notification_sent(task_id, "email", "sent")
    append_event(notification.to_dict())


def kafka_worker() -> None:
    while True:
        try:
            consumer = consume_kafka_events(["report-events"], group_id="notification-service")
            for message in consumer:
                handle_report_generated_event(message.value)
            consumer.close()
        except Exception:
            time.sleep(2)


def start_kafka_worker() -> None:
    thread = threading.Thread(target=kafka_worker, name="notification-kafka-worker", daemon=True)
    thread.start()


class NotificationHandler(JsonHandler):
    service_name = "notification-service"

    def do_GET(self) -> None:
        if self.path == "/responsibility":
            self.send_json(
                200,
                {
                    "service": self.service_name,
                    "subscribes_to": ["ReportGenerated"],
                    "action": "notify user that risk report is ready",
                    "mvp_behavior": "write notification to log",
                },
            )
            return
        if self.path == "/example-event":
            event = notification_sent("task-demo", "email", "sent")
            self.send_json(200, event.to_dict())
            return
        super().do_GET()


if __name__ == "__main__":
    start_kafka_worker()
    run_service(NotificationHandler, 8095)
