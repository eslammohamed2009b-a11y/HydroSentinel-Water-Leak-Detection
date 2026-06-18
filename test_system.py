"""Basic system tests for HydroSentinel.

These tests validate that the diagnostic model bundle can be built/loaded and
that evaluate_telemetry returns a stable output contract for sample telemetry.
"""

from pathlib import Path
import unittest

import pandas as pd

import ml_engine


class HydroSentinelSystemTests(unittest.TestCase):
    """Smoke-level unit tests for core system behavior."""

    @classmethod
    def setUpClass(cls):
        cls.project_dir = Path(__file__).resolve().parent
        cls.model_path = cls.project_dir / "test_hydrosentinel_isolation_forest.joblib"

        cls.normal_group = [
            cls.project_dir / "normal.csv",
            cls.project_dir / "example_normal_day_2026-10-05.csv",
        ]
        cls.event_group = [cls.project_dir / "event.csv"]

        cls.training_df = ml_engine.load_training_labels_for_mode(
            cls.normal_group,
            cls.event_group,
            event_mode=True,
        )
        ml_engine.ensure_diagnostic_model(cls.training_df, cls.model_path)

    @classmethod
    def tearDownClass(cls):
        if cls.model_path.exists():
            cls.model_path.unlink()

    def test_model_bundle_loads_successfully(self):
        """Model bundle should load and contain expected objects."""
        bundle = ml_engine.load_model_bundle(self.model_path)
        self.assertIn("classifier", bundle)
        self.assertIn("regressor", bundle)
        self.assertTrue(bundle.get("diagnostic_mode", False))

    def test_evaluate_telemetry_returns_expected_structure(self):
        """Telemetry evaluation should return expected keys and dataframe."""
        target_df = pd.read_csv(self.project_dir / "event_leak.csv")
        result = ml_engine.evaluate_telemetry(target_df, self.model_path, event_mode=True)

        required_keys = {
            "has_leak",
            "anomalies",
            "df",
            "leak_lpm",
            "max_leak_probability",
            "event_mode",
            "event_rows",
        }
        for key in required_keys:
            self.assertIn(key, result)

        self.assertIsInstance(result["has_leak"], bool)
        self.assertIsInstance(result["df"], pd.DataFrame)
        self.assertGreater(len(result["df"]), 0)


if __name__ == "__main__":
    unittest.main()
