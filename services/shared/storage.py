from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from services.shared.infrastructure import (
    publish_event_to_kafka,
    read_report_from_mongo,
    save_report_to_mongo,
    save_task_to_postgres,
    update_task_status_in_postgres,
)


RUNTIME_DIR = Path(os.environ.get("RUNTIME_DIR", "runtime"))
TASKS_FILE = RUNTIME_DIR / "tasks.json"
EVENTS_FILE = RUNTIME_DIR / "events.jsonl"
REPORTS_DIR = RUNTIME_DIR / "reports"


def ensure_runtime() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def read_tasks() -> dict[str, dict[str, Any]]:
    ensure_runtime()
    if not TASKS_FILE.exists():
        return {}
    return json.loads(TASKS_FILE.read_text(encoding="utf-8"))


def write_tasks(tasks: dict[str, dict[str, Any]]) -> None:
    ensure_runtime()
    TASKS_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


def save_task(task_id: str, task: dict[str, Any]) -> None:
    tasks = read_tasks()
    tasks[task_id] = task
    write_tasks(tasks)
    save_task_to_postgres(task)


def get_task(task_id: str) -> dict[str, Any] | None:
    return read_tasks().get(task_id)


def update_task(task_id: str, **updates: Any) -> dict[str, Any] | None:
    tasks = read_tasks()
    task = tasks.get(task_id)
    if task is None:
        return None
    task.update(updates)
    tasks[task_id] = task
    write_tasks(tasks)
    if "status" in updates:
        update_task_status_in_postgres(task_id, str(updates["status"]))
    return task


def append_event(event: dict[str, Any], publish: bool = True) -> bool:
    ensure_runtime()
    with EVENTS_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False) + "\n")
    if publish:
        return publish_event_to_kafka(event)
    return False


def read_events(limit: int = 100) -> list[dict[str, Any]]:
    ensure_runtime()
    if not EVENTS_FILE.exists():
        return []
    lines = EVENTS_FILE.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines[-limit:] if line.strip()]


def save_report(task_id: str, report: str) -> Path:
    ensure_runtime()
    report_path = REPORTS_DIR / f"{task_id}.md"
    report_path.write_text(report, encoding="utf-8")
    save_report_to_mongo(task_id, report)
    return report_path


def read_report(task_id: str) -> str | None:
    ensure_runtime()
    mongo_report = read_report_from_mongo(task_id)
    if mongo_report:
        return mongo_report
    report_path = REPORTS_DIR / f"{task_id}.md"
    if report_path.exists():
        return report_path.read_text(encoding="utf-8")
    return None
