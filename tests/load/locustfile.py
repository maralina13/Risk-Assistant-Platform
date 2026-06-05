from __future__ import annotations

from random import randint

from locust import HttpUser, between, task


class RiskAssistantUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task(3)
    def submit_project_for_analysis(self) -> None:
        suffix = randint(1000, 9999)
        with self.client.post(
            "/projects/analyze",
            json={
                "project_title": f"Allergy travel app {suffix}",
                "project_description": (
                    "Команда разрабатывает сервис для путешественников с аллергиями: "
                    "карта заведений, фильтры по аллергенам, отзывы, модерация данных, "
                    "планы расширения на несколько стран и интеграция с уведомлениями."
                ),
            },
            name="POST /projects/analyze",
            catch_response=True,
        ) as response:
            if response.status_code in {202, 429}:
                response.success()
            else:
                response.failure(f"unexpected status {response.status_code}")

    @task(1)
    def read_routes(self) -> None:
        self.client.get("/routes", name="GET /routes")

    @task(1)
    def read_missing_report(self) -> None:
        with self.client.get(
            "/reports/load-test-missing",
            name="GET /reports/{missing}",
            catch_response=True,
        ) as response:
            if response.status_code == 404:
                response.success()
            else:
                response.failure(f"unexpected status {response.status_code}")
