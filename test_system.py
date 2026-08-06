"""Focused integration tests for HydroSentinel's finalized API workflow."""

from __future__ import annotations

import os
from pathlib import Path
import unittest

from fastapi.testclient import TestClient


class HydroSentinelBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        project_dir = Path(__file__).resolve().parent
        cls.db_path = project_dir / "test_backend.db"
        if cls.db_path.exists():
            cls.db_path.unlink()
        os.environ.update({
            "DATABASE_URL": f"sqlite:///{cls.db_path.as_posix()}",
            "BOOTSTRAP_ADMIN_EMAIL": "admin@hydrosentinel.app",
            "BOOTSTRAP_ADMIN_PASSWORD": "ChangeMe123!",
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

    def test_health_login_refresh_and_current_user(self):
        self.assertEqual(self.client.get("/api/v1/health").status_code, 200)
        login = self.client.post("/api/v1/auth/login", json={"email": "admin@hydrosentinel.app", "password": "ChangeMe123!"})
        self.assertEqual(login.status_code, 200)
        tokens = login.json()
        self.assertEqual(self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}).status_code, 200)
        self.assertEqual(self.client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code, 200)

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
