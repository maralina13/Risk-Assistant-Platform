from __future__ import annotations

import os

from services.shared.http_client import request_json
from services.shared.http_service import JsonHandler, run_service
from services.shared.infrastructure import check_rate_limit


class ApiGatewayHandler(JsonHandler):
    service_name = "api-gateway"
    requests_by_client: dict[str, int] = {}
    project_intake_url = os.environ.get("PROJECT_INTAKE_URL", "http://localhost:8091")
    report_service_url = os.environ.get("REPORT_SERVICE_URL", "http://localhost:8093")
    audit_service_url = os.environ.get("AUDIT_SERVICE_URL", "http://localhost:8094")

    def do_GET(self) -> None:
        if self.path == "/routes":
            self.send_json(
                200,
                {
                    "service": self.service_name,
                    "routes": {
                        "POST /projects/analyze": "project-intake-service",
                        "GET /tasks/{task_id}/status": "project-intake-service",
                        "GET /reports/{task_id}": "report-service",
                        "GET /admin/audit/{task_id}": "audit-service",
                    },
                    "infrastructure": ["load_balancer", "rate_limiter", "redis_or_valkey"],
                    "load_balancer_port": "http://localhost:8080",
                    "direct_gateway_port": "http://localhost:8088",
                },
            )
            return
        if self.path.startswith("/tasks/") and self.path.endswith("/status"):
            status, body = request_json("GET", f"{self.project_intake_url}{self.path}")
            self.send_json(status, body)
            return
        if self.path.startswith("/reports/"):
            status, body = request_json("GET", f"{self.report_service_url}{self.path}")
            self.send_json(status, body)
            return
        if self.path == "/admin/audit/events":
            status, body = request_json("GET", f"{self.audit_service_url}/events")
            self.send_json(status, body)
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/projects/analyze":
            super().do_POST()
            return

        client_id = self.client_address[0]
        allowed, request_count, limiter_backend = check_rate_limit(client_id, limit=5, window_seconds=60)
        if limiter_backend == "memory_fallback":
            request_count = self.requests_by_client.get(client_id, 0) + 1
            self.requests_by_client[client_id] = request_count
            allowed = request_count <= 5
        if not allowed:
            self.send_json(
                429,
                {
                    "error": "rate_limit_exceeded",
                    "limit": 5,
                    "window_seconds": 60,
                    "rate_limiter": limiter_backend,
                },
            )
            return

        try:
            body = self.read_json()
        except ValueError:
            self.send_json(400, {"error": "invalid_json"})
            return

        project_description = str(body.get("project_description", "")).strip()
        if len(project_description) < 30:
            self.send_json(400, {"error": "project_description_too_short"})
            return

        status, response = request_json("POST", f"{self.project_intake_url}/projects/analyze", body)
        if isinstance(response, dict):
            response["routed_to"] = "project-intake-service"
            response["rate_limiter"] = limiter_backend
        self.send_json(status, response)


if __name__ == "__main__":
    run_service(ApiGatewayHandler, 8088)
