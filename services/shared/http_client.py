from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def request_json(method: str, url: str, body: dict[str, Any] | None = None, timeout: int = 10) -> tuple[int, dict[str, Any]]:
    payload = None
    headers = {"Accept": "application/json"}
    if body is not None:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"

    request = Request(url=url, data=payload, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            data = response.read().decode("utf-8")
            return response.status, json.loads(data) if data else {}
    except HTTPError as error:
        data = error.read().decode("utf-8")
        return error.code, json.loads(data) if data else {"error": "http_error"}
