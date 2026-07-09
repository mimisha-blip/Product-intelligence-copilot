#!/usr/bin/env python3
"""Generate SignalDesk mock CSV datasets for the Product Intelligence Copilot."""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'

CUSTOMER_TYPES = ['New', 'Returning', 'Enterprise Admin', 'Trial User', 'Support Manager']
SERVICE_AREAS = ['Support', 'Sales', 'Product', 'Delivery', 'Billing', 'Onboarding']
SENTIMENTS = ['positive', 'neutral', 'negative']
CUSTOMERS = [
    'Atlas Systems',
    'BrightPath',
    'NexGen',
    'SecureNet',
    'TeamFlow',
    'Vertex Labs',
    'CloudWave',
    'Acme Corp',
    'Northstar Retail',
    'BluePeak Software',
]
ASSIGNEES = ['Mina', 'Jordan', 'Kai', 'Sarah', 'Priya', 'Noah', 'Alex']
JIRA_STATUSES = ['Backlog', 'In Progress', 'In Review', 'Planned', 'Done']
LINEAR_STATUSES = ['Todo', 'Backlog', 'In Progress', 'In Review', 'Planned']
PRIORITIES = ['Low', 'Medium', 'High', 'Critical']
IMPACTS = ['Low', 'Medium', 'High']

SUPPORT_ISSUES = [
    'AI reply draft used the wrong customer context',
    'Omnichannel inbox failed to sync social messages',
    'SLA alert did not notify the escalation owner',
    'Help center article search returned stale content',
    'Conversation assignment rules skipped priority tickets',
    'Customer portal login failed after invite',
    'Billing plan change blocked an account admin',
    'Webhook delivery failed for CRM handoff',
    'Team inbox mentions did not trigger notifications',
    'Duplicate customer profiles appeared after import',
]

FEEDBACK_THEMES = {
    'Support': [
        'SignalDesk helps our agents answer faster, but the AI summaries need clearer source links.',
        'The shared inbox is useful, but escalations are hard to track once tickets move teams.',
        'SLA reminders are helpful, though urgent tickets still need stronger alerts.',
        'The AI reply drafts save time when they include the right product context.',
    ],
    'Sales': [
        'Sales needs cleaner handoff notes when a support thread becomes an expansion opportunity.',
        'The CRM sync is valuable, but deal context is sometimes missing from customer timelines.',
        'We want account health signals surfaced before renewal calls.',
        'SignalDesk should make it easier to see which support issues affect open deals.',
    ],
    'Product': [
        'The feedback clustering view makes roadmap planning easier.',
        'Product teams need stronger links between feedback themes and Jira or Linear issues.',
        'The product insights dashboard should show repeated requests by segment.',
        'We like the trend summaries, but need confidence scores for AI-generated themes.',
    ],
    'Delivery': [
        'Implementation teams need clearer onboarding milestones inside SignalDesk.',
        'Customer launch delays are hard to diagnose from the current timeline.',
        'The onboarding checklist should adapt to customer size and plan.',
        'Delivery status updates should be visible to support managers.',
    ],
    'Billing': [
        'Billing questions should route directly to the right operations queue.',
        'Plan change requests need better audit history.',
        'Invoice disputes are difficult to connect to related support conversations.',
        'Admins want clearer warnings before changing seats or billing tiers.',
    ],
    'Onboarding': [
        'New users understand the inbox quickly, but automation setup feels confusing.',
        'The first-run checklist helps, but it should recommend templates by team type.',
        'Trial users need examples before configuring routing rules.',
        'Setup guidance should explain how AI features use customer data.',
    ],
}

USAGE_METRICS = [
    'Weekly active support managers',
    'AI draft acceptance rate',
    'Median first response time',
    'Onboarding checklist completion',
    'Escalation resolution time',
    'Help center deflection rate',
    'CRM handoff completion',
    'Feedback theme review rate',
]

USAGE_TRENDS = [
    'Up 18% this month',
    'Down 12% after week 2',
    'Stable',
    'Improving steadily',
    'Declining in the last quarter',
]

SEGMENTS = [
    'New onboarding users',
    'Support managers',
    'Enterprise accounts',
    'Trial accounts',
    'Sales-assisted customers',
    'All users',
]

COMPETITOR_INSIGHTS = {
    'Zendesk': [
        'Expanded AI agent capabilities for automated ticket resolution',
        'Bundled workforce management with enterprise support plans',
        'Improved help center search and content recommendations',
    ],
    'Intercom': [
        'Promoted AI-first customer service workflows',
        'Released stronger customer messaging automation',
        'Added product tour and onboarding improvements',
    ],
    'Freshdesk': [
        'Reduced pricing pressure with a mid-market helpdesk bundle',
        'Expanded omnichannel routing for email chat and social support',
        'Improved ticket analytics for support operations teams',
    ],
    'Front': [
        'Launched collaboration features for shared customer inboxes',
        'Improved account-level visibility for customer operations teams',
        'Added workflow automation for high-volume team inboxes',
    ],
    'Help Scout': [
        'Positioned simple support workflows for growing teams',
        'Improved self-service knowledge base management',
        'Promoted lighter-weight customer support operations',
    ],
    'Salesforce Service Cloud': [
        'Deepened CRM-native service automation for enterprise teams',
        'Added Einstein-powered service recommendations',
        'Expanded customer 360 support analytics',
    ],
}

COMPETITOR_NOTES = [
    'SignalDesk should emphasize product-feedback-to-roadmap traceability.',
    'This raises expectations for AI transparency and source citations.',
    'Could increase pricing pressure in SMB and mid-market deals.',
    'The roadmap should highlight faster onboarding and setup guidance.',
    'Support managers may expect stronger omnichannel routing controls.',
    'Enterprise buyers may compare CRM integration depth more closely.',
]


def random_date() -> str:
    start = datetime(2026, 1, 1)
    end = datetime(2026, 6, 28)
    return (start + timedelta(days=random.randint(0, (end - start).days))).strftime('%Y-%m-%d')


def random_week() -> str:
    return f'2026-W{random.randint(1, 52):02d}'


def generate_customer_feedback(count: int) -> list[dict[str, object]]:
    rows = []
    for idx in range(count):
        area = random.choice(SERVICE_AREAS)
        sentiment = random.choices(SENTIMENTS, weights=[0.34, 0.24, 0.42])[0]
        base_score = {'positive': 5, 'neutral': 3, 'negative': 2}[sentiment]
        satisfaction_score = max(1, min(5, base_score + random.choice([-1, 0, 0, 1])))
        rows.append({
            'comment_id': idx + 1,
            'customer_type': random.choice(CUSTOMER_TYPES),
            'service_area': area,
            'comment_text': random.choice(FEEDBACK_THEMES[area]),
            'sentiment': sentiment,
            'satisfaction_score': satisfaction_score,
            'resolution_needed': 1 if sentiment == 'negative' or satisfaction_score <= 2 else 0,
        })
    return rows


def generate_support_cases(count: int) -> list[dict[str, str]]:
    rows = []
    for idx in range(count):
        priority = random.choices(PRIORITIES, weights=[0.18, 0.36, 0.30, 0.16])[0]
        status = random.choices(['Open', 'Pending', 'Resolved', 'Escalated'], weights=[0.25, 0.20, 0.38, 0.17])[0]
        rows.append({
            'id': f's{idx + 1:03d}',
            'case_number': f'SC-{1001 + idx}',
            'customer': random.choice(CUSTOMERS),
            'issue': random.choice(SUPPORT_ISSUES),
            'priority': priority,
            'created_at': random_date(),
            'status': status,
        })
    return rows


def generate_jira_tickets(count: int) -> list[dict[str, str]]:
    themes = [
        ('Add AI reply draft source citations', 'ai;trust;support'),
        ('Improve omnichannel inbox routing', 'inbox;routing;automation'),
        ('Stabilize customer timeline CRM sync', 'crm;integration;timeline'),
        ('Improve feedback theme clustering accuracy', 'feedback;ml;roadmap'),
        ('Automate support SLA escalation workflows', 'sla;workflow;alerts'),
        ('Tune help center search relevance', 'help-center;search'),
        ('Recommend onboarding templates by team type', 'onboarding;templates;activation'),
        ('Add billing audit trail for plan changes', 'billing;audit;admin'),
        ('Build conversation assignment rule debugger', 'automation;debugging;support'),
        ('Create account health signal dashboard', 'analytics;retention;sales'),
    ]
    rows = []
    for idx in range(count):
        title, tags = random.choice(themes)
        rows.append({
            'id': f'j{idx + 1:03d}',
            'key': f'JIRA-{201 + idx}',
            'summary': title,
            'status': random.choice(JIRA_STATUSES),
            'created_at': random_date(),
            'assignee': random.choice(ASSIGNEES),
            'tags': tags,
        })
    return rows


def generate_linear_issues(count: int) -> list[dict[str, str]]:
    issues = [
        ('Add citations to AI-generated ticket summaries', 'AI Platform', 'ai;citations;trust'),
        ('Reduce inbox sync latency for social channels', 'Messaging', 'omnichannel;sync;performance'),
        ('Build escalation owner timeline view', 'Support Ops', 'sla;escalation;timeline'),
        ('Create adaptive onboarding checklist', 'Growth', 'onboarding;activation'),
        ('Improve duplicate profile merge workflow', 'Platform', 'identity;profiles'),
        ('Add CRM handoff completeness score', 'Integrations', 'crm;sales;handoff'),
        ('Create product feedback evidence panel', 'Product Intelligence', 'feedback;roadmap;evidence'),
        ('Improve billing plan change warnings', 'Admin', 'billing;admin;audit'),
        ('Add automation rule simulation mode', 'Workflow Automation', 'automation;debugging'),
        ('Expose account health alerts for PMs', 'Analytics', 'retention;usage;health'),
    ]
    rows = []
    for idx in range(count):
        title, team, labels = random.choice(issues)
        rows.append({
            'id': f'l{idx + 1:03d}',
            'issue_key': f'LIN-{301 + idx}',
            'title': title,
            'status': random.choice(LINEAR_STATUSES),
            'priority': random.choices(PRIORITIES, weights=[0.12, 0.35, 0.36, 0.17])[0],
            'team': team,
            'created_at': random_date(),
            'assignee': random.choice(ASSIGNEES),
            'labels': labels,
        })
    return rows


def generate_usage_analytics(count: int) -> list[dict[str, str]]:
    notes = [
        'AI drafts are adopted fastest by teams with mature help center content',
        'Enterprise admins review product feedback themes before roadmap planning',
        'Trial users drop off when automation setup is skipped',
        'Support managers rely on escalation analytics during weekly reviews',
        'CRM handoff completion improves renewal preparation',
        'Slow inbox sync correlates with lower support manager satisfaction',
        'Knowledge base deflection improves after article recommendations',
        'Account health dashboards are viewed most before renewal cycles',
    ]
    rows = []
    for idx in range(count):
        rows.append({
            'id': f'u{idx + 1:03d}',
            'metric': random.choice(USAGE_METRICS),
            'trend': random.choice(USAGE_TRENDS),
            'period': random_week(),
            'affected_segment': random.choice(SEGMENTS),
            'notes': random.choice(notes),
        })
    return rows


def generate_competitor_insights(count: int) -> list[dict[str, str]]:
    rows = []
    competitors = list(COMPETITOR_INSIGHTS.keys())
    for idx in range(count):
        competitor = random.choice(competitors)
        rows.append({
            'id': f'c{idx + 1:03d}',
            'competitor': competitor,
            'insight': random.choice(COMPETITOR_INSIGHTS[competitor]),
            'impact': random.choices(IMPACTS, weights=[0.20, 0.45, 0.35])[0],
            'source_date': random_date(),
            'notes': random.choice(COMPETITOR_NOTES),
        })
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open(mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    datasets = [
        (
            'customer_feedback.csv',
            ['comment_id', 'customer_type', 'service_area', 'comment_text', 'sentiment', 'satisfaction_score', 'resolution_needed'],
            generate_customer_feedback(500),
        ),
        (
            'support_cases.csv',
            ['id', 'case_number', 'customer', 'issue', 'priority', 'created_at', 'status'],
            generate_support_cases(150),
        ),
        (
            'jira_tickets.csv',
            ['id', 'key', 'summary', 'status', 'created_at', 'assignee', 'tags'],
            generate_jira_tickets(200),
        ),
        (
            'linear_issues.csv',
            ['id', 'issue_key', 'title', 'status', 'priority', 'team', 'created_at', 'assignee', 'labels'],
            generate_linear_issues(30),
        ),
        (
            'usage_analytics.csv',
            ['id', 'metric', 'trend', 'period', 'affected_segment', 'notes'],
            generate_usage_analytics(120),
        ),
        (
            'competitor_insights.csv',
            ['id', 'competitor', 'insight', 'impact', 'source_date', 'notes'],
            generate_competitor_insights(50),
        ),
    ]

    for filename, fieldnames, rows in datasets:
        write_csv(DATA_DIR / filename, fieldnames, rows)

    print('Generated SignalDesk CSV datasets:')
    for filename, _fieldnames, rows in datasets:
        print(f' - data/{filename} ({len(rows)} rows)')


if __name__ == '__main__':
    main()
