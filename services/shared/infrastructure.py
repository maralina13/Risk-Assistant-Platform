from __future__ import annotations

import json
import os
import time
from typing import Any, Iterable


EVENT_TOPICS = {
    "ProjectSubmitted": "project-events",
    "RiskAnalysisStarted": "analysis-events",
    "RiskAnalysisCompleted": "analysis-events",
    "RiskAnalysisFailed": "analysis-events",
    "ReportGenerated": "report-events",
    "NotificationSent": "audit-events",
}


def kafka_bootstrap_servers() -> str:
    return os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")


def publish_event_to_kafka(event: dict[str, Any]) -> bool:
    topic = EVENT_TOPICS.get(str(event.get("event_type", "")))
    if not topic:
        return False

    try:
        from kafka import KafkaProducer

        producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers(),
            value_serializer=lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8"),
            retries=2,
        )
        producer.send(topic, event)
        producer.flush(timeout=5)
        producer.close()
        return True
    except Exception:
        return False


def consume_kafka_events(topics: Iterable[str], group_id: str):
    from kafka import KafkaConsumer

    return KafkaConsumer(
        *topics,
        bootstrap_servers=kafka_bootstrap_servers(),
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        consumer_timeout_ms=1000,
    )


def postgres_dsn() -> str:
    return os.environ.get(
        "POSTGRES_DSN",
        "postgresql://risk_user:risk_password@postgres:5432/risk_assistant",
    )


def save_task_to_postgres(task: dict[str, Any]) -> bool:
    try:
        import psycopg

        with psycopg.connect(postgres_dsn()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO projects (id, title, description)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET title = EXCLUDED.title,
                        description = EXCLUDED.description
                    """,
                    (
                        task["task_id"],
                        task.get("project_title", "Untitled project"),
                        task.get("project_description", ""),
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO analysis_tasks (id, project_id, status, correlation_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET status = EXCLUDED.status,
                        finished_at = CASE
                            WHEN EXCLUDED.status = 'completed' THEN CURRENT_TIMESTAMP
                            ELSE analysis_tasks.finished_at
                        END
                    """,
                    (
                        task["task_id"],
                        task["task_id"],
                        task.get("status", "pending"),
                        task["task_id"],
                    ),
                )
        return True
    except Exception:
        return False


def update_task_status_in_postgres(task_id: str, status: str) -> bool:
    try:
        import psycopg

        with psycopg.connect(postgres_dsn()) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE analysis_tasks
                    SET status = %s,
                        started_at = CASE
                            WHEN %s = 'running' AND started_at IS NULL THEN CURRENT_TIMESTAMP
                            ELSE started_at
                        END,
                        finished_at = CASE
                            WHEN %s = 'completed' THEN CURRENT_TIMESTAMP
                            ELSE finished_at
                        END
                    WHERE id = %s
                    """,
                    (status, status, status, task_id),
                )
        return True
    except Exception:
        return False


def mongo_uri() -> str:
    return os.environ.get("MONGO_URI", "mongodb://mongo:27017")


def save_report_to_mongo(task_id: str, report: str) -> bool:
    try:
        from pymongo import MongoClient

        client = MongoClient(mongo_uri(), serverSelectionTimeoutMS=1500)
        collection = client["risk_assistant"]["reports"]
        collection.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "task_id": task_id,
                    "format": "markdown",
                    "report": report,
                    "updated_at": time.time(),
                }
            },
            upsert=True,
        )
        client.close()
        return True
    except Exception:
        return False


def read_report_from_mongo(task_id: str) -> str | None:
    try:
        from pymongo import MongoClient

        client = MongoClient(mongo_uri(), serverSelectionTimeoutMS=1500)
        document = client["risk_assistant"]["reports"].find_one({"task_id": task_id})
        client.close()
        if not document:
            return None
        return str(document.get("report") or "")
    except Exception:
        return None


def redis_url() -> str:
    return os.environ.get("REDIS_URL", "redis://redis:6379/0")


def check_rate_limit(client_id: str, limit: int, window_seconds: int) -> tuple[bool, int, str]:
    try:
        import redis

        cache = redis.Redis.from_url(redis_url(), decode_responses=True)
        key = f"rate-limit:{client_id}"
        count = int(cache.incr(key))
        if count == 1:
            cache.expire(key, window_seconds)
        return count <= limit, count, "valkey"
    except Exception:
        return True, 1, "memory_fallback"
