import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "generate_mock_data.py"


EXPECTED_HEADERS = {
    "customer_feedback.csv": [
        "id",
        "date",
        "customer_segment",
        "product_area",
        "sentiment",
        "severity",
        "feature_request",
        "description",
        "revenue_impact",
        "region",
    ],
    "jira_tickets.csv": [
        "ticket_id",
        "issue_type",
        "priority",
        "status",
        "product_area",
        "summary",
        "effort_points",
    ],
    "support_cases.csv": [
        "case_id",
        "severity",
        "status",
        "product_area",
        "issue_summary",
        "resolution_status",
    ],
    "competitor_insights.csv": [
        "competitor_name",
        "feature",
        "launch_date",
        "source_type",
        "insight",
        "threat_level",
    ],
    "usage_analytics.csv": [
        "account_id",
        "product_area",
        "weekly_active_users",
        "feature_adoption_rate",
        "churn_risk",
        "nps_score",
    ],
}

EXPECTED_ROW_COUNTS = {
    "customer_feedback.csv": 500,
    "jira_tickets.csv": 200,
    "support_cases.csv": 100,
    "competitor_insights.csv": 50,
    "usage_analytics.csv": 300,
}


class GenerateMockDataTest(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("generate_mock_data", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_generates_requested_raw_csvs_with_coherent_product_areas(self):
        module = self.load_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            (output_dir / "linear_issues.csv").write_text("stale,data\n1,old\n", encoding="utf-8")
            module.generate_all(output_dir)

            generated_files = {path.name for path in output_dir.glob("*.csv")}
            self.assertEqual(set(EXPECTED_HEADERS), generated_files)

            observed_areas = set()
            for filename, expected_header in EXPECTED_HEADERS.items():
                path = output_dir / filename
                self.assertTrue(path.exists(), f"{filename} was not generated")

                with path.open(newline="", encoding="utf-8") as csvfile:
                    rows = list(csv.DictReader(csvfile))

                self.assertEqual(expected_header, list(rows[0].keys()))
                self.assertEqual(EXPECTED_ROW_COUNTS[filename], len(rows))
                if "product_area" in expected_header:
                    observed_areas.update(row["product_area"] for row in rows)

            self.assertIn("Dashboard", observed_areas)
            self.assertIn("AI Assistant", observed_areas)
            self.assertIn("Reporting", observed_areas)
            self.assertEqual(module.PRODUCT_AREAS, sorted(observed_areas))


if __name__ == "__main__":
    unittest.main()
