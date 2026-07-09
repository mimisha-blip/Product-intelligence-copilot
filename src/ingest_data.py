#!/usr/bin/env python3
"""Load raw SignalDesk CSV rows as LangChain Documents."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from langchain_core.documents import Document
except ImportError:
    try:
        from langchain.schema import Document
    except ImportError:

        class Document:  # type: ignore[no-redef]
            def __init__(self, page_content: str, metadata: dict[str, Any]) -> None:
                self.page_content = page_content
                self.metadata = metadata


RAW_DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

PRODUCT_AREA_HINTS = {
    "Dashboard": ["dashboard", "analytics"],
    "Integrations": ["integration", "integrations", "crm", "connector", "marketplace"],
    "Reporting": ["report", "reporting", "export"],
    "AI Assistant": ["ai", "assistant", "copilot", "citation"],
    "Authentication": ["authentication", "sso", "saml", "login"],
    "Billing": ["billing", "invoice", "seat", "plan"],
    "Mobile App": ["mobile", "push"],
    "Notifications": ["notification", "alert", "sla"],
}


def clean_value(value: Any) -> str:
    return "" if value is None else str(value).strip()


def source_type_from_path(path: Path) -> str:
    return path.stem


def infer_product_area(row: dict[str, str]) -> str:
    product_area = clean_value(row.get("product_area"))
    if product_area:
        return product_area

    searchable_text = " ".join(clean_value(value).lower() for value in row.values())
    for area, hints in PRODUCT_AREA_HINTS.items():
        if any(hint in searchable_text for hint in hints):
            return area
    return "Unknown"


def row_id(source_type: str, row: dict[str, str], index: int) -> str:
    for key in ["id", "ticket_id", "case_id", "account_id"]:
        value = clean_value(row.get(key))
        if value:
            return value
    competitor = clean_value(row.get("competitor_name"))
    feature = clean_value(row.get("feature"))
    if competitor and feature:
        return f"{source_type}-{index}"
    return f"{source_type}-{index}"


def row_date(row: dict[str, str]) -> str:
    for key in ["date", "launch_date", "created_at", "source_date"]:
        value = clean_value(row.get(key))
        if value:
            return value
    return ""


def build_metadata(source_type: str, row: dict[str, str], index: int) -> dict[str, str]:
    metadata = {
        "source_type": source_type,
        "product_area": infer_product_area(row),
        "id": row_id(source_type, row, index),
    }

    date_value = row_date(row)
    if date_value:
        metadata["date"] = date_value

    severity = clean_value(row.get("severity"))
    if severity:
        metadata["severity"] = severity

    priority = clean_value(row.get("priority")) or clean_value(row.get("threat_level"))
    if priority:
        metadata["priority"] = priority

    return metadata


def summarize_customer_feedback(row: dict[str, str]) -> str:
    return (
        f"Customer feedback {clean_value(row.get('id'))} from a "
        f"{clean_value(row.get('customer_segment'))} customer in {clean_value(row.get('region'))} "
        f"concerns {clean_value(row.get('product_area'))}. Sentiment is {clean_value(row.get('sentiment'))} "
        f"with {clean_value(row.get('severity'))} severity and {clean_value(row.get('revenue_impact'))} "
        f"revenue impact. Requested feature: {clean_value(row.get('feature_request'))}. "
        f"Description: {clean_value(row.get('description'))}"
    )


def summarize_jira_ticket(row: dict[str, str]) -> str:
    return (
        f"Jira ticket {clean_value(row.get('ticket_id'))} is a {clean_value(row.get('issue_type'))} "
        f"for {clean_value(row.get('product_area'))}. Priority is {clean_value(row.get('priority'))}, "
        f"status is {clean_value(row.get('status'))}, and estimated effort is "
        f"{clean_value(row.get('effort_points'))} points. Summary: {clean_value(row.get('summary'))}"
    )


def summarize_support_case(row: dict[str, str]) -> str:
    return (
        f"Support case {clean_value(row.get('case_id'))} affects {clean_value(row.get('product_area'))}. "
        f"Severity is {clean_value(row.get('severity'))}, status is {clean_value(row.get('status'))}, "
        f"and resolution status is {clean_value(row.get('resolution_status'))}. "
        f"Issue: {clean_value(row.get('issue_summary'))}"
    )


def summarize_competitor_insight(row: dict[str, str]) -> str:
    return (
        f"Competitor insight from {clean_value(row.get('competitor_name'))}: "
        f"they launched or promoted {clean_value(row.get('feature'))} on "
        f"{clean_value(row.get('launch_date'))}. Source type is {clean_value(row.get('source_type'))}. "
        f"Threat level is {clean_value(row.get('threat_level'))}. "
        f"Insight: {clean_value(row.get('insight'))}"
    )


def summarize_usage_analytics(row: dict[str, str]) -> str:
    return (
        f"Usage analytics for account {clean_value(row.get('account_id'))} in "
        f"{clean_value(row.get('product_area'))}: weekly active users are "
        f"{clean_value(row.get('weekly_active_users'))}, feature adoption rate is "
        f"{clean_value(row.get('feature_adoption_rate'))} percent, churn risk is "
        f"{clean_value(row.get('churn_risk'))}, and NPS score is {clean_value(row.get('nps_score'))}."
    )


def summarize_row(source_type: str, row: dict[str, str]) -> str:
    summarizers = {
        "customer_feedback": summarize_customer_feedback,
        "jira_tickets": summarize_jira_ticket,
        "support_cases": summarize_support_case,
        "competitor_insights": summarize_competitor_insight,
        "usage_analytics": summarize_usage_analytics,
    }
    summarizer = summarizers.get(source_type)
    if summarizer:
        return summarizer(row)

    fields = [f"{key}: {clean_value(value)}" for key, value in row.items() if clean_value(value)]
    return f"{source_type} row with " + "; ".join(fields)


def load_documents(raw_data_dir: Path | str = RAW_DATA_DIR) -> list[Document]:
    raw_path = Path(raw_data_dir)
    documents: list[Document] = []

    for csv_path in sorted(raw_path.glob("*.csv")):
        source_type = source_type_from_path(csv_path)
        with csv_path.open(newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for index, row in enumerate(reader, start=1):
                documents.append(
                    Document(
                        page_content=summarize_row(source_type, row),
                        metadata=build_metadata(source_type, row, index),
                    )
                )

    return documents


def main() -> None:
    documents = load_documents()
    counts = Counter(document.metadata["source_type"] for document in documents)

    print(f"Total documents created: {len(documents)}")
    print("Document count by source_type:")
    for source_type, count in sorted(counts.items()):
        print(f" - {source_type}: {count}")

    print("Sample documents:")
    for document in documents[:3]:
        print(f"- page_content: {document.page_content}")
        print(f"  metadata: {document.metadata}")


if __name__ == "__main__":
    main()
