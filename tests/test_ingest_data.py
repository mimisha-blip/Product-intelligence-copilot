import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "ingest_data.py"


class IngestDataTest(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("ingest_data", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def write_csv(self, path, fieldnames, rows):
        with path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def test_load_documents_builds_content_and_metadata_from_raw_csvs(self):
        module = self.load_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            raw_dir = Path(temp_dir)
            self.write_csv(
                raw_dir / "customer_feedback.csv",
                [
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
                [
                    {
                        "id": "CF-0001",
                        "date": "2026-01-15",
                        "customer_segment": "Enterprise",
                        "product_area": "AI Assistant",
                        "sentiment": "negative",
                        "severity": "High",
                        "feature_request": "AI answers with source citations",
                        "description": "AI summaries need clearer source links.",
                        "revenue_impact": "At Risk",
                        "region": "North America",
                    }
                ],
            )
            self.write_csv(
                raw_dir / "jira_tickets.csv",
                [
                    "ticket_id",
                    "issue_type",
                    "priority",
                    "status",
                    "product_area",
                    "summary",
                    "effort_points",
                ],
                [
                    {
                        "ticket_id": "JIRA-201",
                        "issue_type": "Feature",
                        "priority": "Critical",
                        "status": "In Progress",
                        "product_area": "AI Assistant",
                        "summary": "Add source citations to AI Assistant summaries",
                        "effort_points": "8",
                    }
                ],
            )

            documents = module.load_documents(raw_dir)

            self.assertEqual(2, len(documents))
            first = documents[0]
            self.assertIn("AI Assistant", first.page_content)
            self.assertIn("AI summaries need clearer source links.", first.page_content)
            self.assertEqual("customer_feedback", first.metadata["source_type"])
            self.assertEqual("AI Assistant", first.metadata["product_area"])
            self.assertEqual("High", first.metadata["severity"])
            self.assertEqual("2026-01-15", first.metadata["date"])
            self.assertEqual("CF-0001", first.metadata["id"])

            second = documents[1]
            self.assertIn("Add source citations", second.page_content)
            self.assertEqual("jira_tickets", second.metadata["source_type"])
            self.assertEqual("Critical", second.metadata["priority"])
            self.assertEqual("JIRA-201", second.metadata["id"])


if __name__ == "__main__":
    unittest.main()
