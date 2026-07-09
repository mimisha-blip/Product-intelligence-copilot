#!/usr/bin/env python3
"""Generate coherent B2B SaaS mock data for SignalDesk RAG demos."""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

RANDOM_SEED = 42
DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "raw"

PRODUCT_AREAS = sorted([
    "Dashboard",
    "Integrations",
    "Reporting",
    "AI Assistant",
    "Authentication",
    "Billing",
    "Mobile App",
    "Notifications",
])

CUSTOMER_SEGMENTS = ["Enterprise", "Mid-Market", "SMB", "Startup", "Strategic"]
REGIONS = ["North America", "EMEA", "APAC", "LATAM"]
SENTIMENTS = ["positive", "neutral", "negative"]
SEVERITIES = ["Low", "Medium", "High", "Critical"]
REVENUE_IMPACTS = ["Low", "Medium", "High", "At Risk"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
STATUSES = ["Backlog", "Planned", "In Progress", "In Review", "Done"]
ISSUE_TYPES = ["Bug", "Feature", "Tech Debt", "Research", "Improvement"]
SUPPORT_STATUSES = ["Open", "Pending", "Resolved", "Escalated"]
RESOLUTION_STATUSES = ["Unresolved", "Workaround Provided", "Resolved", "Linked to Roadmap"]
CHURN_RISKS = ["Low", "Medium", "High"]
SOURCE_TYPES = ["Release Notes", "Customer Call", "Analyst Report", "Pricing Page", "Product Blog"]
THREAT_LEVELS = ["Low", "Medium", "High"]

COMPETITORS = [
    "Zendesk",
    "Intercom",
    "Freshdesk",
    "Front",
    "Help Scout",
    "Salesforce Service Cloud",
]

AREA_THEMES = {
    "Dashboard": {
        "request": "custom executive widgets",
        "pain": "Dashboard filters reset when managers switch between account views.",
        "jira": "Persist dashboard filters across saved account views",
        "competitor": "executive analytics dashboard",
    },
    "Integrations": {
        "request": "deeper CRM and warehouse sync controls",
        "pain": "CRM handoff records occasionally miss the latest support context.",
        "jira": "Improve CRM sync retry handling and handoff completeness",
        "competitor": "expanded CRM marketplace connectors",
    },
    "Reporting": {
        "request": "scheduled revenue-risk reports",
        "pain": "Large revenue-impact reports time out during leadership reviews.",
        "jira": "Optimize scheduled reporting exports for enterprise accounts",
        "competitor": "automated board-ready reporting pack",
    },
    "AI Assistant": {
        "request": "AI answers with source citations",
        "pain": "AI Assistant summaries are useful but do not always cite the source ticket.",
        "jira": "Add source citations to AI Assistant summaries",
        "competitor": "AI support copilot with verified citations",
    },
    "Authentication": {
        "request": "more flexible SSO setup",
        "pain": "SAML setup errors block new enterprise admins during rollout.",
        "jira": "Add guided SAML setup validation for enterprise admins",
        "competitor": "self-serve SSO configuration wizard",
    },
    "Billing": {
        "request": "clearer seat and plan change previews",
        "pain": "Admins cannot preview invoice impact before changing seats.",
        "jira": "Add billing impact preview before plan changes",
        "competitor": "usage-based billing controls",
    },
    "Mobile App": {
        "request": "mobile escalation approvals",
        "pain": "Mobile users cannot approve urgent escalations from push notifications.",
        "jira": "Support mobile escalation approval actions",
        "competitor": "native mobile support command center",
    },
    "Notifications": {
        "request": "better notification routing rules",
        "pain": "Critical SLA alerts are noisy for managers who own multiple queues.",
        "jira": "Improve notification routing for critical SLA alerts",
        "competitor": "smart SLA notification routing",
    },
}


def random_date(start: date = date(2026, 1, 1), days: int = 180) -> str:
    return (start + timedelta(days=random.randint(0, days))).isoformat()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def weighted_area(index: int) -> str:
    if index % 7 == 0:
        return "AI Assistant"
    if index % 5 == 0:
        return "Reporting"
    if index % 4 == 0:
        return "Integrations"
    return random.choice(PRODUCT_AREAS)


def generate_customer_feedback(count: int = 500) -> list[dict[str, object]]:
    rows = []
    for idx in range(1, count + 1):
        area = weighted_area(idx)
        theme = AREA_THEMES[area]
        severity = random.choices(SEVERITIES, weights=[20, 35, 30, 15])[0]
        sentiment = random.choices(SENTIMENTS, weights=[30, 25, 45])[0]
        revenue_impact = "At Risk" if severity == "Critical" else random.choice(REVENUE_IMPACTS[:-1])
        rows.append({
            "id": f"CF-{idx:04d}",
            "date": random_date(),
            "customer_segment": random.choice(CUSTOMER_SEGMENTS),
            "product_area": area,
            "sentiment": sentiment,
            "severity": severity,
            "feature_request": theme["request"],
            "description": theme["pain"],
            "revenue_impact": revenue_impact,
            "region": random.choice(REGIONS),
        })
    return rows


def generate_jira_tickets(count: int = 200) -> list[dict[str, object]]:
    rows = []
    for idx in range(1, count + 1):
        area = weighted_area(idx)
        rows.append({
            "ticket_id": f"JIRA-{idx + 200}",
            "issue_type": random.choice(ISSUE_TYPES),
            "priority": random.choices(PRIORITIES, weights=[15, 35, 35, 15])[0],
            "status": random.choice(STATUSES),
            "product_area": area,
            "summary": AREA_THEMES[area]["jira"],
            "effort_points": random.choice([1, 2, 3, 5, 8, 13]),
        })
    return rows


def generate_support_cases(count: int = 100) -> list[dict[str, object]]:
    rows = []
    for idx in range(1, count + 1):
        area = weighted_area(idx)
        severity = random.choices(SEVERITIES, weights=[15, 30, 35, 20])[0]
        rows.append({
            "case_id": f"SC-{idx + 1000}",
            "severity": severity,
            "status": "Escalated" if severity == "Critical" else random.choice(SUPPORT_STATUSES),
            "product_area": area,
            "issue_summary": AREA_THEMES[area]["pain"],
            "resolution_status": "Linked to Roadmap" if severity in ["High", "Critical"] else random.choice(RESOLUTION_STATUSES),
        })
    return rows


def generate_competitor_insights(count: int = 50) -> list[dict[str, object]]:
    rows = []
    for idx in range(1, count + 1):
        area = weighted_area(idx)
        competitor = random.choice(COMPETITORS)
        threat = "High" if area in ["AI Assistant", "Reporting", "Integrations"] else random.choice(THREAT_LEVELS)
        rows.append({
            "competitor_name": competitor,
            "feature": AREA_THEMES[area]["competitor"],
            "launch_date": random_date(),
            "source_type": random.choice(SOURCE_TYPES),
            "insight": f"{competitor} is positioning {AREA_THEMES[area]['competitor']} as a reason to switch from slower B2B SaaS tools.",
            "threat_level": threat,
        })
    return rows


def generate_usage_analytics(count: int = 300) -> list[dict[str, object]]:
    rows = []
    for idx in range(1, count + 1):
        area = weighted_area(idx)
        high_risk_area = area in ["Reporting", "AI Assistant", "Integrations"]
        adoption = random.randint(22, 58) if high_risk_area else random.randint(48, 91)
        churn_risk = "High" if adoption < 40 else random.choice(["Low", "Medium"])
        rows.append({
            "account_id": f"ACC-{idx:04d}",
            "product_area": area,
            "weekly_active_users": random.randint(12, 850),
            "feature_adoption_rate": adoption,
            "churn_risk": churn_risk,
            "nps_score": random.randint(8, 35) if churn_risk == "High" else random.randint(36, 72),
        })
    return rows


def generate_all(output_dir: Path = DATA_ROOT) -> None:
    random.seed(RANDOM_SEED)
    datasets = [
        (
            "customer_feedback.csv",
            ["id", "date", "customer_segment", "product_area", "sentiment", "severity", "feature_request", "description", "revenue_impact", "region"],
            generate_customer_feedback(),
        ),
        (
            "jira_tickets.csv",
            ["ticket_id", "issue_type", "priority", "status", "product_area", "summary", "effort_points"],
            generate_jira_tickets(),
        ),
        (
            "support_cases.csv",
            ["case_id", "severity", "status", "product_area", "issue_summary", "resolution_status"],
            generate_support_cases(),
        ),
        (
            "competitor_insights.csv",
            ["competitor_name", "feature", "launch_date", "source_type", "insight", "threat_level"],
            generate_competitor_insights(),
        ),
        (
            "usage_analytics.csv",
            ["account_id", "product_area", "weekly_active_users", "feature_adoption_rate", "churn_risk", "nps_score"],
            generate_usage_analytics(),
        ),
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale_csv in output_dir.glob("*.csv"):
        stale_csv.unlink()

    for filename, fieldnames, rows in datasets:
        write_csv(output_dir / filename, fieldnames, rows)

    print(f"Generated SignalDesk mock data in {output_dir}")
    for filename, _fieldnames, rows in datasets:
        print(f" - {filename}: {len(rows)} rows")


def main() -> None:
    generate_all()


if __name__ == "__main__":
    main()
