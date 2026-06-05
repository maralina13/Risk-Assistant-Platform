from __future__ import annotations

import threading
import time
from typing import Any

from services.shared.http_service import JsonHandler, run_service
from services.shared.infrastructure import consume_kafka_events
from services.shared.storage import append_event, read_events


AUDIT_TOPICS = ["project-events", "analysis-events", "report-events", "audit-events"]


def handle_audit_event(event: dict[str, Any]) -> None:
    if not event.get("event_id") or not event.get("event_type"):
        return
    append_event(event, publish=False)


def kafka_worker() -> None:
    while True:
        try:
            consumer = consume_kafka_events(AUDIT_TOPICS, group_id="audit-service")
            for message in consumer:
                handle_audit_event(message.value)
            consumer.close()
        except Exception:
            time.sleep(2)


def start_kafka_worker() -> None:
    thread = threading.Thread(target=kafka_worker, name="audit-kafka-worker", daemon=True)
    thread.start()


class AuditHandler(JsonHandler):
    service_name = "audit-service"

    def do_GET(self) -> None:
        if self.path == "/topics":
            self.send_json(
                200,
                {
                    "service": self.service_name,
                    "subscribes_to": [
                        "ProjectSubmitted",
                        "RiskAnalysisStarted",
                        "RiskAnalysisCompleted",
                        "RiskAnalysisFailed",
                        "ReportGenerated",
                        "NotificationSent",
                    ],
                    "stores": ["audit trail", "latency", "errors", "correlation_id"],
                },
            )
            return
        if self.path == "/events":
            self.send_json(200, {"events": read_events()})
            return
        super().do_GET()


if __name__ == "__main__":
    start_kafka_worker()
    run_service(AuditHandler, 8094)
