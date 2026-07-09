import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "answer_generator.py"


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
        return FakeCompletionResponse("Executive Summary: Prioritize Reporting and AI Assistant.")


class FakeChat:
    def __init__(self, calls):
        self.completions = FakeCompletions(calls)


class FakeOpenAI:
    instances = []

    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.completion_calls = []
        self.chat = FakeChat(self.completion_calls)
        FakeOpenAI.instances.append(self)


class AnswerGeneratorTest(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("answer_generator", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_generate_answer_uses_retrieved_context_and_fireworks_model(self):
        module = self.load_module()
        matches = [
            {
                "score": 0.91,
                "metadata": {
                    "text": "Reporting exports time out for enterprise customers.",
                    "source_type": "customer_feedback",
                    "product_area": "Reporting",
                    "severity": "High",
                    "id": "CF-0001",
                },
            },
            {
                "score": 0.88,
                "metadata": {
                    "text": "AI Assistant summaries lack source citations.",
                    "source_type": "support_cases",
                    "product_area": "AI Assistant",
                    "priority": "Critical",
                    "id": "SC-1001",
                },
            },
        ]
        retriever_calls = []

        def fake_get_retriever(k):
            retriever_calls.append(k)

            def retrieve(query):
                self.assertEqual("Which features should we prioritize?", query)
                return matches

            return retrieve

        FakeOpenAI.instances.clear()
        with patch.dict(
            os.environ,
            {
                "FIREWORKS_API_KEY": "fireworks-key",
                "FIREWORKS_MODEL": "accounts/fireworks/models/qwen-test",
            },
        ):
            with patch.object(module, "OpenAI", FakeOpenAI):
                with patch.object(module, "get_retriever", fake_get_retriever):
                    answer = module.generate_answer("Which features should we prioritize?")

        self.assertEqual("Executive Summary: Prioritize Reporting and AI Assistant.", answer)
        self.assertEqual([5], retriever_calls)
        client = FakeOpenAI.instances[0]
        self.assertEqual("fireworks-key", client.api_key)
        self.assertEqual("https://api.fireworks.ai/inference/v1", client.base_url)
        call = client.completion_calls[0]
        self.assertEqual("accounts/fireworks/models/qwen-test", call["model"])
        self.assertEqual(0.2, call["temperature"])
        prompt = call["messages"][1]["content"]
        self.assertIn("Which features should we prioritize?", prompt)
        self.assertIn("Reporting exports time out", prompt)
        self.assertIn("source_type=customer_feedback", prompt)
        self.assertIn("product_area=AI Assistant", prompt)
        self.assertIn("Executive summary", prompt)
        self.assertIn("Risks or tradeoffs", prompt)


if __name__ == "__main__":
    unittest.main()
