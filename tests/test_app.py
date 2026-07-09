import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "app.py"


class AppTest(unittest.TestCase):
    def fake_streamlit(self, submitted=False, question=""):
        fake_streamlit = types.SimpleNamespace(
            set_page_config=Mock(),
            markdown=Mock(),
            title=Mock(),
            caption=Mock(),
            sidebar=types.SimpleNamespace(
                header=Mock(),
                button=Mock(return_value=False),
                markdown=Mock(),
            ),
            session_state={},
            form=Mock(),
            text_input=Mock(return_value=question),
            form_submit_button=Mock(return_value=submitted),
            spinner=Mock(),
            error=Mock(),
            info=Mock(),
            expander=Mock(),
            write=Mock(),
        )
        fake_streamlit.form.return_value.__enter__ = Mock(return_value=fake_streamlit)
        fake_streamlit.form.return_value.__exit__ = Mock(return_value=False)
        fake_streamlit.spinner.return_value.__enter__ = Mock(return_value=fake_streamlit)
        fake_streamlit.spinner.return_value.__exit__ = Mock(return_value=False)
        fake_streamlit.expander.return_value.__enter__ = Mock(return_value=fake_streamlit)
        fake_streamlit.expander.return_value.__exit__ = Mock(return_value=False)
        return fake_streamlit

    def test_app_imports_run_graph_and_defines_main(self):
        fake_streamlit = self.fake_streamlit()
        fake_graph = types.SimpleNamespace(run_graph=Mock(return_value="answer"))
        sys.modules["streamlit"] = fake_streamlit
        sys.modules["graph"] = fake_graph
        try:
            spec = importlib.util.spec_from_file_location("app", MODULE_PATH)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            sys.modules.pop("streamlit", None)
            sys.modules.pop("graph", None)

        self.assertIs(module.run_graph, fake_graph.run_graph)
        self.assertTrue(callable(module.main))

    def test_app_renders_route_answer_and_sources_from_graph_response(self):
        fake_streamlit = self.fake_streamlit(
            submitted=True,
            question="Which features should we prioritize?",
        )
        graph_response = {
            "question": "Which features should we prioritize?",
            "route": "prioritization",
            "answer": "Prioritize Reporting.",
            "sources": [
                {
                    "source_type": "customer_feedback",
                    "product_area": "Reporting",
                    "severity_or_priority": "High",
                    "page_content": "Reporting exports timeout for enterprise customers.",
                }
            ],
        }
        fake_graph = types.SimpleNamespace(run_graph=Mock(return_value=graph_response))
        sys.modules["streamlit"] = fake_streamlit
        sys.modules["graph"] = fake_graph
        try:
            spec = importlib.util.spec_from_file_location("app", MODULE_PATH)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.main()
        finally:
            sys.modules.pop("streamlit", None)
            sys.modules.pop("graph", None)

        fake_graph.run_graph.assert_called_once_with("Which features should we prioritize?")
        rendered_markdown = "\n".join(str(call.args[0]) for call in fake_streamlit.markdown.call_args_list)
        self.assertIn("Route selected", rendered_markdown)
        self.assertIn("prioritization", rendered_markdown)
        self.assertIn("AI Recommendation", rendered_markdown)
        self.assertIn("Prioritize Reporting.", rendered_markdown)
        self.assertIn("Retrieved Evidence", rendered_markdown)
        fake_streamlit.expander.assert_called_once()
        rendered_write = "\n".join(str(call.args[0]) for call in fake_streamlit.write.call_args_list)
        self.assertIn("customer_feedback", rendered_write)
        self.assertIn("Reporting exports timeout", rendered_write)


if __name__ == "__main__":
    unittest.main()
