#!/usr/bin/env python3
"""Generate product-manager answers from retrieved RAG context using Fireworks."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rag_pipeline import get_retriever


FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"
DEFAULT_QUESTIONS = [
    "What are the top customer pain points?",
    "Which features should we prioritize?",
    "Generate a Q3 roadmap.",
    "What are competitors doing that we are not?",
]


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing {name}. Add it to .env or export it in your shell.")
    return value


def load_environment() -> tuple[str, str]:
    load_dotenv(PROJECT_ROOT / ".env")
    fireworks_api_key = require_env("FIREWORKS_API_KEY")
    fireworks_model = require_env("FIREWORKS_MODEL")
    return fireworks_api_key, fireworks_model


def match_metadata(match: Any) -> dict[str, Any]:
    return match.get("metadata", {}) if isinstance(match, dict) else match.metadata


def match_score(match: Any) -> Any:
    return match.get("score", "") if isinstance(match, dict) else getattr(match, "score", "")


def format_context(matches: list[Any]) -> str:
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


def build_prompt(question: str, context: str) -> str:
    return f"""You are a senior B2B SaaS product manager helping with roadmap decisions.

Use only the retrieved context below. Do not invent facts that are not supported by the context.

Question:
{question}

Retrieved context:
{context}

Write a product-manager style answer with these sections:
1. Executive summary
2. Direct answer
3. Evidence from retrieved data
4. Product recommendation
5. Risks or tradeoffs
"""


def generate_answer(question: str) -> str:
    retriever = get_retriever(k=5)
    matches = retriever(question)
    context = format_context(matches)
    fireworks_api_key, fireworks_model = load_environment()

    client = OpenAI(
        api_key=fireworks_api_key,
        base_url=FIREWORKS_BASE_URL,
    )
    response = client.chat.completions.create(
        model=fireworks_model,
        messages=[
            {
                "role": "system",
                "content": "You answer as a concise, evidence-driven product strategy copilot.",
            },
            {
                "role": "user",
                "content": build_prompt(question, context),
            },
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content


def main() -> None:
    for question in DEFAULT_QUESTIONS:
        print("=" * 80)
        print(f"Question: {question}")
        print("-" * 80)
        print(generate_answer(question))
        print()


if __name__ == "__main__":
    main()
