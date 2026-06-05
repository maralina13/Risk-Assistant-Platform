from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Event:
    event_type: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=utc_now)
    version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def project_submitted(task_id: str, project_description: str, project_title: str | None = None) -> Event:
    return Event(
        event_type="ProjectSubmitted",
        payload={
            "task_id": task_id,
            "project_title": project_title,
            "project_description": project_description,
            "status": "pending",
        },
    )


def risk_analysis_started(task_id: str, llm_mode: str) -> Event:
    return Event(
        event_type="RiskAnalysisStarted",
        payload={
            "task_id": task_id,
            "llm_mode": llm_mode,
            "status": "running",
        },
    )


def risk_analysis_completed(task_id: str, report_id: str, risk_count: int) -> Event:
    return Event(
        event_type="RiskAnalysisCompleted",
        payload={
            "task_id": task_id,
            "report_id": report_id,
            "risk_count": risk_count,
            "status": "completed",
        },
    )


def risk_analysis_failed(task_id: str, error_code: str, error_message: str, retryable: bool) -> Event:
    return Event(
        event_type="RiskAnalysisFailed",
        payload={
            "task_id": task_id,
            "error_code": error_code,
            "error_message": error_message,
            "retryable": retryable,
            "status": "failed",
        },
    )


def report_generated(task_id: str, report_path: str) -> Event:
    return Event(
        event_type="ReportGenerated",
        payload={
            "task_id": task_id,
            "report_path": report_path,
        },
    )


def notification_sent(task_id: str, channel: str, status: str) -> Event:
    return Event(
        event_type="NotificationSent",
        payload={
            "task_id": task_id,
            "channel": channel,
            "status": status,
        },
    )
