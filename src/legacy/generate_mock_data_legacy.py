#!/usr/bin/env python3
import json
import random
from datetime import datetime, timedelta

sources = [
    ('feedback', 'Customer Feedback'),
    ('support', 'Support Cases'),
    ('jira', 'Jira Tickets'),
    ('usage', 'Usage Data'),
    ('competitor', 'Competitor Notes'),
]

titles = {
    'feedback': [
        'Customers request mobile offline mode',
        'Users ask for dark mode in dashboard',
        'Clients want multi-language support',
        'Teams request better collaboration comments',
    ],
    'support': [
        'Support case: onboarding setup confusion',
        'Support case: payment failure during checkout',
        'Support case: notifications not arriving',
        'Support case: permission error for guest users',
    ],
    'jira': [
        'JIRA-324: Add bulk import for product catalogs',
        'JIRA-412: Improve search relevance for tags',
        'JIRA-289: Optimize page load time for reports',
        'JIRA-501: Migrate billing flow to new API',
    ],
    'usage': [
        'Usage trend: feature adoption drops after week 2',
        'Usage trend: high preview abandonment in onboarding',
        'Usage trend: power users rely on exports heavily',
        'Usage trend: daily active users spike on Mondays',
    ],
    'competitor': [
        'Competitor A launched AI recommendation assistant',
        'Competitor B added a freemium tier for SMBs',
        'Competitor C reduced pricing for integrations',
        'Competitor D announced a new analytics module',
    ],
}

summaries = {
    'feedback': [
        'Multiple enterprise customers want offline editing for on-the-go usage.',
        'End users want a more accessible UI and text size controls.',
        'Customers are asking for faster shared board updates.',
    ],
    'support': [
        'New customers struggle with the admin setup flow and permission model.',
        'Several cases report missing email alerts during onboarding.',
        'Users repeatedly open cases around billing plan changes.',
    ],
    'jira': [
        'Product team asked for bulk import to reduce manual entry time.',
        'This ticket aims to improve search performance for large datasets.',
        'Engineering backlog includes several UX polish stories.',
    ],
    'usage': [
        'Active users drop by 25% after the second week for the new onboarding workflow.',
        'Most accounts complete initial setup but fail to return for advanced collaboration.',
        'Export usage spikes during customer review cycles.',
    ],
    'competitor': [
        'This new capability creates pressure on roadmap differentiation.',
        'A lower-price plan may shift smaller customers rapidly.',
        'Competitor messaging emphasizes speed and ease of setup.',
    ],
}

details = {
    'feedback': [
        'Field teams need access while disconnected. This is a top request in NPS comments.',
        'Users want to save drafts and resume offline without losing progress.',
        'Small-business customers want localized product terminology and support docs.',
    ],
    'support': [
        'Cases show repeated questions around workspace roles, API keys, and first project creation.',
        'There are several tickets about account verification delays and forgotten passwords.',
        'Support notes mention inconsistent mobile push notifications across devices.',
    ],
    'jira': [
        'A Jira epic is open to evaluate CSV/Excel upload and integrate with current catalog APIs.',
        'The engineering spike will validate alternatives for indexing and caching.',
        'The request is tied to the upcoming enterprise release cycle.',
    ],
    'usage': [
        'Retention drops after feature discovery, especially among trial accounts.',
        'Users who complete setup are twice as likely to adopt advanced reporting.',
        'The analytics page is the most common exit point during onboarding.',
    ],
    'competitor': [
        'This move raises the bar for AI-assisted recommendations in our category.',
        'The competitor product still lacks deep workflow automation, which is our opportunity.',
        'The new analytics module may shift customer expectations toward embedded reporting.',
    ],
}

tags = {
    'feedback': [['mobile', 'offline'], ['usability', 'accessibility'], ['collaboration', 'feedback']],
    'support': [['onboarding', 'usability'], ['billing', 'payment'], ['notifications', 'roles']],
    'jira': [['productivity', 'import'], ['search', 'performance'], ['engineering', 'backend']],
    'usage': [['retention', 'onboarding'], ['behavior', 'export'], ['analytics', 'adoption']],
    'competitor': [['AI', 'strategy'], ['pricing', 'market'], ['analytics', 'differentiation']],
}


def random_date(days_back=30):
    return (datetime.now() - timedelta(days=random.randint(0, days_back))).strftime('%Y-%m-%d')


def build_item(source_type, idx):
    title = random.choice(titles[source_type])
    return {
        'id': f'{source_type[0]}{idx + 1}',
        'source': source_type,
        'title': title,
        'summary': random.choice(summaries[source_type]),
        'createdAt': random_date(45),
        'tags': random.choice(tags[source_type]),
        'details': random.choice(details[source_type]),
    }


def generate_items(count=20):
    items = []
    for i in range(count):
        source_type, _ = random.choice(sources)
        items.append(build_item(source_type, i))
    return items


def main():
    dataset = generate_items(20)
    out_path = 'src/data.ts'
    with open(out_path, 'w', encoding='utf-8') as outfile:
        outfile.write('import type { DataItem } from "./types";\n\n')
        outfile.write('export const sampleData: DataItem[] = [\n')
        for item in dataset:
            outfile.write('  {\n')
            outfile.write(f'    id: "{item["id"]}",\n')
            outfile.write(f'    source: "{item["source"]}",\n')
            outfile.write(f'    title: "{item["title"]}",\n')
            outfile.write(f'    summary: "{item["summary"]}",\n')
            outfile.write(f'    createdAt: "{item["createdAt"]}",\n')
            outfile.write('    tags: [')
            outfile.write(', '.join(f'"{tag}"' for tag in item['tags']))
            outfile.write('],\n')
            outfile.write(f'    details: "{item["details"]}",\n')
            outfile.write('  },\n')
        outfile.write('];\n')

    print(f'Generated {len(dataset)} mock items into {out_path}')


if __name__ == '__main__':
    main()
