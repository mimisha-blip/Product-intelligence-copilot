#!/usr/bin/env python3
"""LangGraph workflow for routing product intelligence questions."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rag_pipeline import get_retriever
from scoring import calculate_priority_scores


FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"
DEFAULT_QUESTIONS = [
    "What are the top customer pain points?",
    "Which features should we prioritize?",
    "Generate a Q3 roadmap.",
    "What are competitors doing that we are not?",
]


class GraphState(TypedDict):
    question: str
    route: str
    retrieved_context: str
    retrieved_documents: list[object]
    sources: list[dict[str, str]]
    final_answer: str


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing {name}. Add it to .env or export it in your shell.")
    return value


def load_fireworks_environment() -> tuple[str, str]:
    load_dotenv(PROJECT_ROOT / ".env")
    return require_env("FIREWORKS_API_KEY"), require_env("FIREWORKS_MODEL")


def router_node(state: GraphState) -> dict[str, str]:
    question = state["question"].lower()
    if any(keyword in question for keyword in ["pain", "complaint", "issue", "problem"]):
        route = "pain_points"
    elif any(keyword in question for keyword in ["prioritize", "priority", "feature", "build next"]):
        route = "prioritization"
    elif any(keyword in question for keyword in ["roadmap", "q3", "plan"]):
        route = "roadmap"
    elif any(keyword in question for keyword in ["competitor", "gap", "market"]):
        route = "competitor"
    else:
        route = "fallback"
    return {"route": route}


def match_metadata(match: Any) -> dict[str, Any]:
    return match.get("metadata", {}) if isinstance(match, dict) else match.metadata


def match_score(match: Any) -> Any:
    return match.get("score", "") if isinstance(match, dict) else getattr(match, "score", "")


def match_page_content(match: Any, metadata: dict[str, Any]) -> str:
    if isinstance(match, dict):
        return str(metadata.get("text", ""))
    return str(getattr(match, "page_content", "") or metadata.get("text", ""))


def source_from_match(match: Any) -> dict[str, str]:
    metadata = match_metadata(match)
    return {
        "source_type": str(metadata.get("source_type", "")),
        "product_area": str(metadata.get("product_area", "")),
        "severity_or_priority": str(metadata.get("severity") or metadata.get("priority") or ""),
        "page_content": match_page_content(match, metadata),
    }


def format_retrieved_context(matches: list[Any]) -> str:
    context_blocks = []
    for index, match in enumerate(matches, start=1):
        metadata = match_metadata(match)
        severity_or_priority = metadata.get("severity") or metadata.get("priority") or ""
        context_blocks.append(
            "\n".join([
                f"[{index}] score={match_score(match)}",
                f"source_type={metadata.get('source_type')}",
                f"product_area={metadata.get('product_area')}",
                f"severity_or_priority={severity_or_priority}",
                f"id={metadata.get('id')}",
                f"text={metadata.get('text', '')}",
            ])
        )
    return "\n\n".join(context_blocks)


def retrieval_node(state: GraphState) -> dict[str, Any]:
    retriever = get_retriever(k=5)
    matches = retriever(state["question"])
    return {
        "retrieved_context": format_retrieved_context(matches),
        "retrieved_documents": matches,
        "sources": [source_from_match(match) for match in matches],
    }


def call_qwen(question: str, context: str, answer_format: str) -> str:
    fireworks_api_key, fireworks_model = load_fireworks_environment()
    client = OpenAI(api_key=fireworks_api_key, base_url=FIREWORKS_BASE_URL)
    prompt = f"""You are a senior B2B SaaS product manager.

Use only the retrieved context. Do not invent facts.

Question:
{question}

Retrieved context:
{context}

Answer in this exact format:
{answer_format}
"""
    response = client.chat.completions.create(
        model=fireworks_model,
        messages=[
            {
                "role": "system",
                "content": "You are an evidence-driven product intelligence copilot.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content


def pain_points_node(state: GraphState) -> dict[str, str]:
    answer_format = """- Top pain points
- Evidence
- Customer impact
- Recommendation"""
    return {
        "final_answer": call_qwen(state["question"], state["retrieved_context"], answer_format)
    }


def prioritization_node(state: GraphState) -> dict[str, str]:
    ranked_scores = calculate_priority_scores(state.get("retrieved_documents", []))
    priority_table = "No scoreable documents found."
    if not ranked_scores.empty:
        priority_table = ranked_scores.to_string(index=False)

    context = f"""{state["retrieved_context"]}

Priority score table:
{priority_table}
"""
    answer_format = """- Recommended priorities
- Why these features
- Impact vs effort
- Tradeoffs"""
    question = (
        f"{state['question']}\n\n"
        "Explain the recommendation using both the retrieved evidence and the priority score table."
    )
    return {
        "final_answer": call_qwen(question, context, answer_format)
    }


def roadmap_node(state: GraphState) -> dict[str, str]:
    answer_format = """- Q3 roadmap by month
- Themes
- Dependencies
- Risks"""
    return {
        "final_answer": call_qwen(state["question"], state["retrieved_context"], answer_format)
    }


def competitor_node(state: GraphState) -> dict[str, str]:
    answer_format = """- Competitor moves
- Gaps
- Risk level
- Recommended response"""
    return {
        "final_answer": call_qwen(state["question"], state["retrieved_context"], answer_format)
    }


def fallback_node(state: GraphState) -> dict[str, str]:
    answer_format = """- Clarifying interpretation
- Relevant evidence
- Suggested next question"""
    return {
        "final_answer": call_qwen(state["question"], state["retrieved_context"], answer_format)
    }


def route_after_retrieval(state: GraphState) -> str:
    return state["route"]


def build_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("router_node", router_node)
    workflow.add_node("retrieval_node", retrieval_node)
    workflow.add_node("pain_points", pain_points_node)
    workflow.add_node("prioritization", prioritization_node)
    workflow.add_node("roadmap", roadmap_node)
    workflow.add_node("competitor", competitor_node)
    workflow.add_node("fallback", fallback_node)

    workflow.add_edge(START, "router_node")
    workflow.add_edge("router_node", "retrieval_node")
    workflow.add_conditional_edges(
        "retrieval_node",
        route_after_retrieval,
        {
            "pain_points": "pain_points",
            "prioritization": "prioritization",
            "roadmap": "roadmap",
            "competitor": "competitor",
            "fallback": "fallback",
        },
    )
    workflow.add_edge("pain_points", END)
    workflow.add_edge("prioritization", END)
    workflow.add_edge("roadmap", END)
    workflow.add_edge("competitor", END)
    workflow.add_edge("fallback", END)
    return workflow.compile()


def run_graph(question: str) -> dict[str, Any]:
    graph = build_graph()
    final_state = graph.invoke({
        "question": question,
        "route": "",
        "retrieved_context": "",
        "retrieved_documents": [],
        "sources": [],
        "final_answer": "",
    })
    return {
        "question": final_state["question"],
        "route": final_state["route"],
        "answer": final_state["final_answer"],
        "sources": final_state["sources"],
    }


def run_graph_with_state(question: str) -> GraphState:
    graph = build_graph()
    return graph.invoke({
        "question": question,
        "route": "",
        "retrieved_context": "",
        "retrieved_documents": [],
        "sources": [],
        "final_answer": "",
    })


def main() -> None:
    for question in DEFAULT_QUESTIONS:
        state = run_graph_with_state(question)
        print("=" * 80)
        print(f"Question: {question}")
        print(f"Route selected: {state['route']}")
        print("-" * 80)
        print(state["final_answer"])
        print()


if __name__ == "__main__":
    main()
