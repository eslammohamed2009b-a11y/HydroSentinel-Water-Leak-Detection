"""Backend system tests for HydroSentinel."""

from __future__ import annotations

import os
from pathlib import Path
import unittest

from fastapi.testclient import TestClient


class HydroSentinelBackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project_dir = Path(__file__).resolve().parent
        cls.db_path = cls.project_dir / "test_backend.db"
        if cls.db_path.exists():
            cls.db_path.unlink()

        os.environ["DATABASE_URL"] = f"sqlite:///{cls.db_path.as_posix()}"
        os.environ["BOOTSTRAP_ADMIN_EMAIL"] = "admin@hydrosentinel.app"
        os.environ["BOOTSTRAP_ADMIN_PASSWORD"] = "ChangeMe123!"
        os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000"

        from backend.main import app

        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        from backend.database.session import engine

        engine.dispose()
        if cls.db_path.exists():
            cls.db_path.unlink()

    def test_health_endpoint_returns_ok(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_auth_login_and_me_flow(self):
        login_response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "admin@hydrosentinel.app", "password": "ChangeMe123!"},
        )
        self.assertEqual(login_response.status_code, 200)
        payload = login_response.json()
        self.assertIn("access_token", payload)
        self.assertIn("refresh_token", payload)

        me_response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {payload['access_token']}"},
        )
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()["email"], "admin@hydrosentinel.app")

    def test_analysis_endpoints_persist_and_return_feedback(self):
        analysis_response = self.client.post(
            "/api/v1/analyses",
            json={"scenario_selected": "event_leak.csv", "event_mode": True},
        )
        self.assertEqual(analysis_response.status_code, 200)
        analysis_payload = analysis_response.json()
        self.assertTrue(analysis_payload["has_leak"])
        self.assertIn("analysis_id", analysis_payload)

        history_response = self.client.get("/api/v1/analyses")
        self.assertEqual(history_response.status_code, 200)
        self.assertGreaterEqual(len(history_response.json()), 1)

        detail_response = self.client.get(f"/api/v1/analyses/{analysis_payload['analysis_id']}")
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()["analysis_id"], analysis_payload["analysis_id"])

        feedback_response = self.client.post(
            f"/api/v1/analyses/{analysis_payload['analysis_id']}/feedback",
            json={"verdict": "confirmed_alert"},
        )
        self.assertEqual(feedback_response.status_code, 200)
        self.assertEqual(feedback_response.json()["feedback"], "confirmed_alert")

    def test_scenarios_endpoint_returns_seeded_matrix(self):
        response = self.client.get("/api/v1/scenarios")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 4)
        self.assertIn("filename", payload[0])


if __name__ == "__main__":
    unittest.main()
