from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


class JsonHandler(BaseHTTPRequestHandler):
    service_name = "service"

    def read_json(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return {}
        raw_body = self.rfile.read(content_length)
        return json.loads(raw_body.decode("utf-8"))

    def send_json(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def send_text(self, status: int, body: str, content_type: str = "text/plain; charset=utf-8") -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_json(200, {"service": self.service_name, "status": "ok"})
            return
        if self.path == "/metrics":
            metric_service_name = self.service_name.replace("-", "_")
            self.send_text(
                200,
                "\n".join(
                    [
                        "# HELP risk_assistant_service_up Service health exported by the built-in HTTP handler.",
                        "# TYPE risk_assistant_service_up gauge",
                        f'risk_assistant_service_up{{service="{self.service_name}"}} 1',
                        "# HELP risk_assistant_service_info Static service information.",
                        "# TYPE risk_assistant_service_info gauge",
                        f'risk_assistant_service_info{{service="{self.service_name}",service_id="{metric_service_name}"}} 1',
                        "",
                    ]
                ),
                "text/plain; version=0.0.4; charset=utf-8",
            )
            return
        self.send_json(404, {"error": "not_found", "path": self.path})

    def do_POST(self) -> None:
        self.send_json(404, {"error": "not_found", "path": self.path})


def run_service(handler_class: type[JsonHandler], default_port: int) -> None:
    port = int(os.environ.get("PORT", default_port))
    server = ThreadingHTTPServer(("0.0.0.0", port), handler_class)
    print(f"{handler_class.service_name} listening on port {port}")
    server.serve_forever()
