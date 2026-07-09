#!/usr/bin/env python3
"""Score retrieved product evidence for feature prioritization."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd


SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rag_pipeline import get_retriever


FEATURE_AREAS = [
    "Dashboard",
    "Integrations",
    "Reporting",
    "AI Assistant",
    "Authentication",
    "Billing",
    "Mobile App",
    "Notifications",
]

SEVERITY_VALUES = {
    "critical": 5,
    "urgent": 5,
    "p0": 5,
    "high": 4,
    "p1": 4,
    "medium": 2,
    "p2": 2,
    "low": 1,
    "p3": 1,
}

SEGMENT_VALUES = {
    "strategic": 4,
    "enterprise": 4,
    "mid-market": 3,
    "mid market": 3,
    "smb": 2,
    "startup": 1,
}

REVENUE_IMPACT_VALUES = {
    "at risk": 5,
    "high": 4,
    "medium": 2,
    "low": 1,
}

COMPETITOR_THREAT_VALUES = {
    "critical": 5,
    "high": 4,
    "medium": 2,
    "low": 1,
}


def document_metadata(document: Any) -> dict[str, Any]:
    if isinstance(document, dict):
        return dict(document.get("metadata", {}))
    return dict(getattr(document, "metadata", {}) or {})


def document_text(document: Any, metadata: dict[str, Any]) -> str:
    if isinstance(document, dict):
        return str(metadata.get("text", ""))
    return str(getattr(document, "page_content", "") or metadata.get("text", ""))


def normalized(value: Any) -> str:
    return str(value or "").strip().lower()


def first_present(metadata: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = metadata.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def value_from_map(value: str, values: dict[str, int]) -> int:
    value_lower = normalized(value)
    for label, score in values.items():
        if label in value_lower:
            return score
    return 0


def severity_score(metadata: dict[str, Any], text: str) -> int:
    explicit_value = first_present(metadata, ["severity", "priority"])
    explicit_score = value_from_map(explicit_value, SEVERITY_VALUES)
    if explicit_score:
        return explicit_score

    text_lower = normalized(text)
    for label, score in SEVERITY_VALUES.items():
        if re.search(rf"\b{re.escape(label)}\b", text_lower):
            return score
    return 0


def customer_impact_score(metadata: dict[str, Any], text: str) -> int:
    segment = first_present(metadata, ["customer_segment", "segment"])
    revenue_impact = first_present(metadata, ["revenue_impact"])

    text_lower = normalized(text)
    segment_score = value_from_map(segment, SEGMENT_VALUES)
    if not segment_score:
        segment_score = max(
            (score for label, score in SEGMENT_VALUES.items() if label in text_lower),
            default=0,
        )

    revenue_score = value_from_map(revenue_impact, REVENUE_IMPACT_VALUES)
    if not revenue_score:
        revenue_score = max(
            (
                score
                for label, score in REVENUE_IMPACT_VALUES.items()
                if f"{label} revenue impact" in text_lower
            ),
            default=0,
        )

    return segment_score + revenue_score


def competitor_pressure_score(metadata: dict[str, Any], text: str) -> int:
    source_type = normalized(metadata.get("source_type"))
    if "competitor" not in source_type:
        return 0

    threat = first_present(metadata, ["threat_level", "priority", "severity"])
    score = value_from_map(threat, COMPETITOR_THREAT_VALUES)
    if score:
        return score

    text_lower = normalized(text)
    for label, value in COMPETITOR_THREAT_VALUES.items():
        if f"threat level is {label}" in text_lower or f"{label} threat" in text_lower:
            return value
    return 2


def effort_score(metadata: dict[str, Any], text: str) -> int:
    effort = first_present(metadata, ["effort_points", "effort"])
    if effort:
        match = re.search(r"\d+", effort)
        if match:
            return int(match.group(0))

    match = re.search(r"(?:effort is|estimated effort is|estimated effort)\s+(\d+)\s+points", normalized(text))
    if match:
        return int(match.group(1))
    return 0


def recommendation_for(final_score: int) -> str:
    if final_score >= 35:
        return "Prioritize immediately"
    if final_score >= 20:
        return "Prioritize next"
    if final_score >= 10:
        return "Monitor and validate"
    return "Defer unless strategically required"


def empty_scores_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "product_area",
            "frequency_score",
            "severity_score",
            "customer_impact_score",
            "competitor_pressure_score",
            "effort_score",
            "final_score",
            "recommendation",
        ]
    )


def calculate_priority_scores(documents: list[Any]) -> pd.DataFrame:
    """Rank product areas using retrieved RAG evidence."""
    grouped: dict[str, dict[str, int]] = {}

    for document in documents:
        metadata = document_metadata(document)
        text = document_text(document, metadata)
        product_area = str(metadata.get("product_area") or "").strip()
        if product_area not in FEATURE_AREAS:
            continue

        scores = grouped.setdefault(
            product_area,
            {
                "frequency_score": 0,
                "severity_score": 0,
                "customer_impact_score": 0,
                "competitor_pressure_score": 0,
                "effort_score": 0,
            },
        )
        scores["frequency_score"] += 1
        scores["severity_score"] += severity_score(metadata, text)
        scores["customer_impact_score"] += customer_impact_score(metadata, text)
        scores["competitor_pressure_score"] += competitor_pressure_score(metadata, text)
        scores["effort_score"] += effort_score(metadata, text)

    rows = []
    for product_area, scores in grouped.items():
        final_score = (
            scores["frequency_score"] * 2
            + scores["severity_score"] * 3
            + scores["customer_impact_score"] * 2
            + scores["competitor_pressure_score"] * 2
            - scores["effort_score"]
        )
        rows.append({
            "product_area": product_area,
            **scores,
            "final_score": final_score,
            "recommendation": recommendation_for(final_score),
        })

    if not rows:
        return empty_scores_frame()

    return pd.DataFrame(rows).sort_values(
        by=["final_score", "frequency_score", "severity_score"],
        ascending=[False, False, False],
    ).reset_index(drop=True)


def main() -> None:
    query = "Which features should we prioritize?"
    retriever = get_retriever(k=5)
    documents = retriever(query)
    ranked = calculate_priority_scores(documents)

    print(f"Query: {query}")
    print("Ranked priority scores:")
    if ranked.empty:
        print("No scoreable documents found.")
    else:
        print(ranked.to_string(index=False))


if __name__ == "__main__":
    main()
