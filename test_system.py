"""Focused integration tests for HydroSentinel's finalized API workflow."""

from __future__ import annotations

import os
from pathlib import Path
import unittest

from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func
from sqlalchemy import select


class HydroSentinelBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        project_dir = Path(__file__).resolve().parent
        cls.db_path = project_dir / "test_backend.db"
        if cls.db_path.exists():
            cls.db_path.unlink()
        os.environ.update({
            "APP_ENV": "test",
            "DATABASE_URL": f"sqlite:///{cls.db_path.as_posix()}",
            "JWT_SECRET_KEY": "test-only-jwt-secret-that-is-long-enough",
            "BOOTSTRAP_ADMIN_ENABLED": "true",
            "BOOTSTRAP_ADMIN_EMAIL": "admin@hydrosentinel.app",
            "BOOTSTRAP_ADMIN_PASSWORD": "ChangeMe123!",
            "ALLOW_PUBLIC_REGISTRATION": "true",
            "ALLOWED_ORIGINS": "http://localhost:3000",
        })
        from backend.main import app
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        from backend.database.session import engine
        engine.dispose()
        if cls.db_path.exists():
            cls.db_path.unlink()

    def _register_and_login(self, email: str) -> dict[str, str]:
        registered = self.client.post("/api/v1/auth/register", json={"email": email, "full_name": "Facility Operator", "password": "SecurePass123!"})
        self.assertEqual(registered.status_code, 201)
        login = self.client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePass123!"})
        self.assertEqual(login.status_code, 200)
        return {"Authorization": f"Bearer {login.json()['access_token']}"}

    def _artifact_counts(self) -> tuple[int, int]:
        from backend.database.session import SessionLocal
        from backend.models.analysis import AnalysisFeedback
        from backend.models.analysis import AnalysisRun

        session = SessionLocal()
        try:
            return (
                int(session.scalar(select(func.count()).select_from(AnalysisRun)) or 0),
                int(session.scalar(select(func.count()).select_from(AnalysisFeedback)) or 0),
            )
        finally:
            session.close()

    def test_health_login_refresh_and_current_user(self):
        self.assertEqual(self.client.get("/api/v1/health").status_code, 200)
        login = self.client.post("/api/v1/auth/login", json={"email": "admin@hydrosentinel.app", "password": "ChangeMe123!"})
        self.assertEqual(login.status_code, 200)
        tokens = login.json()
        self.assertEqual(self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}).status_code, 200)
        self.assertEqual(self.client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code, 200)

    def test_public_demo_analysis_is_non_persistent(self):
        scenarios = self.client.get("/api/v1/scenarios")
        self.assertEqual(scenarios.status_code, 200)
        self.assertEqual(len(scenarios.json()), 4)

        before = self._artifact_counts()
        response = self.client.post("/api/v1/demo/analyses", json={"scenario_selected": "normal.csv", "event_mode": False})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["analysis_id"])
        self.assertIn("Synthetic/simulated", response.json()["limitation_note"])
        self.assertEqual(before, self._artifact_counts())

        unknown = self.client.post("/api/v1/demo/analyses", json={"scenario_selected": "not-a-scenario.csv", "event_mode": False})
        self.assertEqual(unknown.status_code, 400)
        self.assertEqual(before, self._artifact_counts())
        self.assertEqual(self.client.get("/api/v1/analyses").status_code, 401)

    def test_private_analysis_history_feedback_and_owner_isolation(self):
        first_user = self._register_and_login("first@example.com")
        second_user = self._register_and_login("second@example.com")
        self.assertEqual(self.client.post("/api/v1/analyses", json={"scenario_selected": "normal.csv", "event_mode": False}).status_code, 401)

        normal = self.client.post("/api/v1/analyses", headers=first_user, json={"scenario_selected": "normal.csv", "event_mode": False})
        self.assertEqual(normal.status_code, 200)
        self.assertFalse(normal.json()["has_leak"])
        self.assertIn("Synthetic/simulated", normal.json()["limitation_note"])

        leak = self.client.post("/api/v1/analyses", headers=first_user, json={"scenario_selected": "event_leak.csv", "event_mode": True})
        self.assertEqual(leak.status_code, 200)
        self.assertTrue(leak.json()["has_leak"])
        analysis_id = leak.json()["analysis_id"]
        self.assertGreaterEqual(len(self.client.get("/api/v1/analyses", headers=first_user).json()), 2)
        self.assertEqual(self.client.get(f"/api/v1/analyses/{analysis_id}", headers=second_user).status_code, 404)
        self.assertEqual(self.client.post(f"/api/v1/analyses/{analysis_id}/feedback", headers=second_user, json={"verdict": "false_positive"}).status_code, 404)
        feedback = self.client.post(f"/api/v1/analyses/{analysis_id}/feedback", headers=first_user, json={"verdict": "confirmed_alert"})
        self.assertEqual(feedback.status_code, 200)
        self.assertEqual(feedback.json()["feedback"], "confirmed_alert")

    def test_same_authenticated_scenario_creates_distinct_history_records(self):
        headers = self._register_and_login("repeat@example.com")
        first = self.client.post("/api/v1/analyses", headers=headers, json={"scenario_selected": "normal.csv", "event_mode": False})
        second = self.client.post("/api/v1/analyses", headers=headers, json={"scenario_selected": "normal.csv", "event_mode": False})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertNotEqual(first.json()["analysis_id"], second.json()["analysis_id"])

        history = self.client.get("/api/v1/analyses", headers=headers)
        self.assertEqual(history.status_code, 200)
        history_ids = {item["analysis_id"] for item in history.json()}
        self.assertIn(first.json()["analysis_id"], history_ids)
        self.assertIn(second.json()["analysis_id"], history_ids)

    def test_public_registration_can_be_disabled_without_creating_a_user(self):
        from backend.core.config import settings
        from backend.database.session import SessionLocal
        from backend.models.user import User

        previous_value = settings.allow_public_registration
        settings.allow_public_registration = False
        try:
            response = self.client.post(
                "/api/v1/auth/register",
                json={"email": "disabled@example.com", "full_name": "Disabled User", "password": "SecurePass123!"},
            )
            self.assertEqual(response.status_code, 403)
            session = SessionLocal()
            try:
                self.assertIsNone(session.scalar(select(User).where(User.email == "disabled@example.com")))
            finally:
                session.close()
        finally:
            settings.allow_public_registration = previous_value

    def test_production_rejects_unsafe_security_configuration(self):
        from backend.core.config import Settings

        with self.assertRaises(ValidationError):
            Settings(app_env="production", jwt_secret_key="change-me", bootstrap_admin_enabled=False)

        with self.assertRaises(ValidationError):
            Settings(
                app_env="production",
                jwt_secret_key="a-strong-production-jwt-secret-with-32-characters",
                bootstrap_admin_enabled=True,
                bootstrap_admin_email="admin@hydrosentinel.app",
                bootstrap_admin_password="ChangeMe123!",
            )

    def test_feedback_route_handles_cors_preflight_and_invalid_tokens(self):
        preflight = self.client.options(
            "/api/v1/analyses/sample-analysis-id/feedback",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        self.assertEqual(preflight.status_code, 200)
        self.assertEqual(preflight.headers["access-control-allow-origin"], "http://localhost:3000")
        self.assertIn("authorization", preflight.headers["access-control-allow-headers"])
        self.assertIn("content-type", preflight.headers["access-control-allow-headers"])

        invalid = self.client.post(
            "/api/v1/analyses/sample-analysis-id/feedback",
            headers={
                "Origin": "http://localhost:3000",
                "Authorization": "Bearer invalid-token",
            },
            json={"verdict": "confirmed_alert"},
        )
        self.assertEqual(invalid.status_code, 401)
        self.assertEqual(invalid.json()["detail"], "Invalid token")
        self.assertEqual(invalid.headers["access-control-allow-origin"], "http://localhost:3000")

    def test_event_mode_changes_contextual_handling_and_rejects_bad_input(self):
        headers = self._register_and_login("event@example.com")
        disabled = self.client.post("/api/v1/analyses", headers=headers, json={"scenario_selected": "event.csv", "event_mode": False})
        enabled = self.client.post("/api/v1/analyses", headers=headers, json={"scenario_selected": "event.csv", "event_mode": True})
        self.assertEqual(disabled.status_code, 200)
        self.assertEqual(enabled.status_code, 200)
        self.assertFalse(disabled.json()["event_mode"])
        self.assertTrue(enabled.json()["event_mode"])
        self.assertFalse(enabled.json()["has_leak"])
        malformed = self.client.post("/api/v1/analyses", headers=headers, json={"scenario_selected": "not-a-scenario.csv", "event_mode": False})
        self.assertEqual(malformed.status_code, 400)


if __name__ == "__main__":
    unittest.main()
