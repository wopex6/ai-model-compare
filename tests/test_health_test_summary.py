"""Tests for health profile test results summary report generation."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_compare.medical_advisor_health_context import HealthProfile, HEALTH_DATA_DIR


class TestHealthTestResultsSummary(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.health_dir = Path(self.temp_dir.name)
        self.profile_path = self.health_dir / "test-user.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def _make_profile(self, data):
        self.health_dir.mkdir(parents=True, exist_ok=True)
        profile_file = self.health_dir / "test-user.json"
        with open(profile_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        with patch("ai_compare.medical_advisor_health_context.HEALTH_DATA_DIR", self.health_dir):
            return HealthProfile("test-user")

    def test_empty_profile_summary(self):
        profile = self._make_profile({"user_id": "test-user", "name": "Test User", "test_results": []})
        summary = profile.generate_test_results_summary()

        self.assertFalse(summary["has_results"])
        self.assertEqual(summary["text_report"], "No test results on file.")
        self.assertEqual(summary["overview"]["total_results"], 0)

    def test_summary_groups_latest_and_flags_abnormal(self):
        data = {
            "user_id": "test-user",
            "name": "Jane Doe",
            "test_results": [
                {
                    "test_name": "TSH",
                    "value": "5.8 mIU/L",
                    "reference_range": "0.4 - 4.0",
                    "date": "2026-03-15",
                },
                {
                    "test_name": "TSH (historical)",
                    "value": "4.9 mIU/L",
                    "reference_range": "0.4 - 4.0",
                    "date": "2025-11-01",
                },
                {
                    "test_name": "Vitamin D",
                    "value": "78 nmol/L",
                    "reference_range": "50 - 150",
                    "date": "2026-03-15",
                },
            ],
            "conversation_insights": [
                {
                    "insight": "Latest TSH remains elevated.",
                    "category": "test_results",
                }
            ],
        }
        profile = self._make_profile(data)
        summary = profile.generate_test_results_summary()

        self.assertTrue(summary["has_results"])
        self.assertEqual(summary["overview"]["total_results"], 3)
        self.assertEqual(summary["overview"]["unique_tests"], 2)
        self.assertEqual(summary["overview"]["flagged_count"], 1)
        self.assertEqual(summary["groups"][0]["display_name"], "TSH")
        self.assertEqual(summary["groups"][0]["status"], "high")
        self.assertEqual(summary["groups"][0]["trend"], "up")
        self.assertIn("FLAGGED RESULTS", summary["text_report"])
        self.assertIn("Latest TSH remains elevated.", summary["insights"])


if __name__ == "__main__":
    unittest.main()
