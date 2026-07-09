import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "graph.py"


class FakeChoiceMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeChoiceMessage(content)


class FakeCompletionResponse:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


class FakeCompletions:
    def __init__(self, calls):
        self.calls = calls

    def create(self, model, messages, temperature):
        self.calls.append({
            "model": model,
            "messages": messages,
            "temperature": temperature,
        })
        return FakeCompletionResponse("Graph answer")


class FakeChat:
    def __init__(self, calls):
        self.completions = FakeCompletions(calls)


class FakeOpenAI:
    instances = []

    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.calls = []
        self.chat = FakeChat(self.calls)
        FakeOpenAI.instances.append(self)


class GraphTest(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("graph", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_router_classifies_product_questions(self):
        module = self.load_module()

        self.assertEqual("pain_points", module.router_node({"question": "What pain do customers mention?"})["route"])
        self.assertEqual("prioritization", module.router_node({"question": "Which feature should we build next?"})["route"])
        self.assertEqual("roadmap", module.router_node({"question": "Generate a Q3 roadmap"})["route"])
        self.assertEqual("competitor", module.router_node({"question": "What competitor gap exists?"})["route"])
        self.assertEqual("fallback", module.router_node({"question": "Hello?"})["route"])

    def test_run_graph_routes_retrieves_and_generates_answer(self):
        module = self.load_module()
        matches = [
            {
                "score": 0.8,
                "metadata": {
                    "text": "Billing previews are missing.",
                    "source_type": "customer_feedback",
                    "product_area": "Billing",
                    "severity": "High",
                    "id": "CF-1",
                },
            }
        ]
        retriever_calls = []

        def fake_get_retriever(k):
            retriever_calls.append(k)

            def retrieve(question):
                self.assertEqual("What are the top customer pain points?", question)
                return matches

            return retrieve

        FakeOpenAI.instances.clear()
        with patch.dict(
            os.environ,
            {"FIREWORKS_API_KEY": "fireworks-key", "FIREWORKS_MODEL": "accounts/fireworks/models/qwen3p7-plus"},
        ):
            with patch.object(module, "get_retriever", fake_get_retriever):
                with patch.object(module, "OpenAI", FakeOpenAI):
                    result = module.run_graph("What are the top customer pain points?")

        self.assertEqual("What are the top customer pain points?", result["question"])
        self.assertEqual("pain_points", result["route"])
        self.assertEqual("Graph answer", result["answer"])
        self.assertEqual([
            {
                "source_type": "customer_feedback",
                "product_area": "Billing",
                "severity_or_priority": "High",
                "page_content": "Billing previews are missing.",
            }
        ], result["sources"])
        self.assertEqual([5], retriever_calls)
        call = FakeOpenAI.instances[0].calls[0]
        self.assertEqual("accounts/fireworks/models/qwen3p7-plus", call["model"])
        prompt = call["messages"][1]["content"]
        self.assertIn("Top pain points", prompt)
        self.assertIn("Billing previews are missing.", prompt)
        self.assertIn("source_type=customer_feedback", prompt)
        self.assertIn("Customer impact", prompt)

    def test_prioritization_prompt_includes_priority_score_table(self):
        module = self.load_module()
        matches = [
            {
                "score": 0.8,
                "metadata": {
                    "text": "Reporting exports timeout for enterprise customers.",
                    "source_type": "customer_feedback",
                    "product_area": "Reporting",
                    "severity": "Critical",
                    "id": "CF-2",
                },
            }
        ]
        retriever_calls = []

        def fake_get_retriever(k):
            retriever_calls.append(k)

            def retrieve(question):
                self.assertEqual("Which features should we prioritize?", question)
                return matches

            return retrieve

        class FakeScores:
            empty = False

            def to_string(self, index=False):
                self.index = index
                return "product_area final_score recommendation\nReporting 44 Prioritize immediately"

        score_calls = []

        def fake_calculate_priority_scores(documents):
            score_calls.append(documents)
            return FakeScores()

        FakeOpenAI.instances.clear()
        with patch.dict(
            os.environ,
            {"FIREWORKS_API_KEY": "fireworks-key", "FIREWORKS_MODEL": "accounts/fireworks/models/qwen3p7-plus"},
        ):
            with patch.object(module, "get_retriever", fake_get_retriever):
                with patch.object(module, "calculate_priority_scores", fake_calculate_priority_scores):
                    with patch.object(module, "OpenAI", FakeOpenAI):
                        result = module.run_graph("Which features should we prioritize?")

        self.assertEqual("Graph answer", result["answer"])
        self.assertEqual("prioritization", result["route"])
        self.assertEqual([5], retriever_calls)
        self.assertEqual([matches], score_calls)
        prompt = FakeOpenAI.instances[0].calls[0]["messages"][1]["content"]
        self.assertIn("Priority score table:", prompt)
        self.assertIn("Reporting 44 Prioritize immediately", prompt)
        self.assertIn("retrieved evidence", prompt)
        self.assertIn("priority score table", prompt)


if __name__ == "__main__":
    unittest.main()
