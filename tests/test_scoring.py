import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "scoring.py"


class FakeDocument:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata


class ScoringTest(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("scoring", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_calculate_priority_scores_ranks_by_impact_and_competitor_pressure(self):
        module = self.load_module()
        documents = [
            FakeDocument(
                "Customer feedback from an Enterprise customer has Critical severity and At Risk revenue impact.",
                {
                    "source_type": "customer_feedback",
                    "product_area": "Reporting",
                    "severity": "Critical",
                    "customer_segment": "Enterprise",
                    "revenue_impact": "At Risk",
                },
            ),
            FakeDocument(
                "Competitor insight says a board-ready reporting pack has High threat level.",
                {
                    "source_type": "competitor_insights",
                    "product_area": "Reporting",
                    "priority": "High",
                    "threat_level": "High",
                },
            ),
            FakeDocument(
                "Jira ticket is a Story for Billing. Priority is Medium and estimated effort is 8 points.",
                {
                    "source_type": "jira_tickets",
                    "product_area": "Billing",
                    "priority": "Medium",
                    "effort_points": "8",
                },
            ),
        ]

        ranked = module.calculate_priority_scores(documents)

        self.assertEqual("Reporting", ranked.iloc[0]["product_area"])
        self.assertEqual(2, ranked.iloc[0]["frequency_score"])
        self.assertGreater(ranked.iloc[0]["competitor_pressure_score"], 0)
        self.assertEqual(8, ranked.loc[ranked["product_area"] == "Billing", "effort_score"].iloc[0])
        self.assertIn("Prioritize", ranked.iloc[0]["recommendation"])

    def test_calculate_priority_scores_accepts_pinecone_match_dicts(self):
        module = self.load_module()
        documents = [
            {
                "score": 0.91,
                "metadata": {
                    "source_type": "customer_feedback",
                    "product_area": "AI Assistant",
                    "severity": "High",
                    "text": "Customer feedback from a Strategic customer has High severity and High revenue impact.",
                },
            },
            {
                "score": 0.86,
                "metadata": {
                    "source_type": "jira_tickets",
                    "product_area": "AI Assistant",
                    "priority": "High",
                    "text": "Jira ticket priority is High and estimated effort is 3 points.",
                },
            },
        ]

        ranked = module.calculate_priority_scores(documents)

        self.assertEqual(["AI Assistant"], ranked["product_area"].tolist())
        self.assertEqual(2, ranked.iloc[0]["frequency_score"])
        self.assertEqual(3, ranked.iloc[0]["effort_score"])


if __name__ == "__main__":
    unittest.main()
