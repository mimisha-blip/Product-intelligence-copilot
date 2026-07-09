#!/usr/bin/env python3
"""Streamlit UI for the AI Product Intelligence Copilot."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from graph import run_graph


EXAMPLE_QUESTIONS = [
    "What are the top customer pain points?",
    "Which features should we prioritize?",
    "Generate a Q3 roadmap.",
    "What are competitors doing that we are not?",
]


def set_default_question(question: str) -> None:
    st.session_state["question"] = question


def render_sidebar() -> None:
    st.sidebar.header("Example questions")
    for question in EXAMPLE_QUESTIONS:
        if st.sidebar.button(question, use_container_width=True):
            set_default_question(question)

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "**Data sources used**\n\n"
        "- Customer feedback\n"
        "- Jira tickets\n"
        "- Support cases\n"
        "- Usage analytics\n"
        "- Competitor insights"
    )


def render_how_it_works() -> None:
    st.markdown("### How this works")
    st.markdown(
        "The copilot routes each question through LangGraph, retrieves relevant evidence "
        "from Pinecone, scores prioritization questions when needed, and sends the grounded "
        "context to Qwen on Fireworks."
    )


def render_route(result: dict) -> None:
    route = result.get("route")
    if route:
        st.markdown(f"**Route selected:** `{route}`")


def render_answer(result: dict) -> None:
    st.markdown("### AI Recommendation")
    answer = result.get("answer")
    if answer:
        st.markdown(answer)
    else:
        st.info("Choose an example or enter a product strategy question to generate a recommendation.")


def render_sources(result: dict) -> None:
    sources = result.get("sources") or []
    st.markdown("### Retrieved Evidence")
    if not sources:
        st.info("Retrieved evidence will appear here after you generate a recommendation.")
        return

    for index, source in enumerate(sources, start=1):
        source_type = source.get("source_type", "Unknown source")
        product_area = source.get("product_area", "Unknown area")
        label = f"{index}. {source_type} - {product_area}"
        with st.expander(label):
            st.write(f"**source_type:** {source_type}")
            st.write(f"**product_area:** {product_area}")
            st.write(f"**severity/priority:** {source.get('severity_or_priority', '') or 'Not specified'}")
            st.write(source.get("page_content", ""))


def main() -> None:
    st.set_page_config(
        page_title="AI Product Intelligence Copilot",
        page_icon="",
        layout="wide",
    )

    st.markdown(
        """
        <style>
        .block-container {
            max-width: 980px;
            padding-top: 2.4rem;
        }
        div[data-testid="stSidebar"] button {
            text-align: left;
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    render_sidebar()

    st.title("AI Product Intelligence Copilot")
    st.caption(
        "Ask product strategy questions across customer feedback, Jira tickets, "
        "support cases, usage analytics, and competitor insights."
    )

    with st.form("product_question_form"):
        question = st.text_input(
            "Product strategy question",
            value=st.session_state.get("question", ""),
            placeholder="Which features should we prioritize?",
        )
        submitted = st.form_submit_button("Generate recommendation", use_container_width=True)

    if submitted and question.strip():
        st.session_state["question"] = question.strip()
        with st.spinner("Analyzing product evidence..."):
            try:
                st.session_state["result"] = run_graph(question.strip())
            except Exception as exc:
                st.error(f"Unable to generate a recommendation: {exc}")

    result = st.session_state.get("result", {})
    render_route(result)
    render_answer(result)
    render_sources(result)

    render_how_it_works()

    st.markdown("### Data sources used")
    st.markdown(
        "Customer feedback, Jira tickets, support cases, usage analytics, and competitor insights."
    )


if __name__ == "__main__":
    main()
