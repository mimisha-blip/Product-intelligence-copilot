import type { DataItem } from './types';

export const sampleData: DataItem[] = [
  {
    id: 'f1',
    source: 'feedback',
    title: 'Customers ask for mobile offline mode',
    summary: 'Multiple enterprise customers want offline editing for on-the-go usage.',
    createdAt: '2026-06-18',
    tags: ['mobile', 'offline', 'customer-feedback'],
    details: 'The mobile UX is strong, but field teams need access while disconnected. This is a top request in NPS comments.'
  },
  {
    id: 's1',
    source: 'support',
    title: 'Support case: onboarding setup confusion',
    summary: 'New customers struggle with the admin setup flow and permission model.',
    createdAt: '2026-06-15',
    tags: ['onboarding', 'support', 'usability'],
    details: 'Cases show repeated questions around workspace roles, API keys, and first project creation.'
  },
  {
    id: 'j1',
    source: 'jira',
    title: 'JIRA-188: Add bulk import for product catalogs',
    summary: 'Product team asked for bulk import to reduce manual entry time.',
    createdAt: '2026-06-10',
    tags: ['productivity', 'import', 'engineering'],
    details: 'A Jira epic is open to evaluate CSV/Excel upload and integrate with current catalog APIs.'
  },
  {
    id: 'u1',
    source: 'usage',
    title: 'Usage trend: feature adoption drops after week 2',
    summary: 'Active users drop by 25% after the second week for the new onboarding workflow.',
    createdAt: '2026-06-20',
    tags: ['usage', 'retention', 'onboarding'],
    details: 'Most accounts complete initial setup but fail to return for advanced collaboration features.'
  },
  {
    id: 'c1',
    source: 'competitor',
    title: 'Competitor A launched AI recommendation assistant',
    summary: 'Competitor A now suggests feature prioritization using usage signals.',
    createdAt: '2026-06-14',
    tags: ['competitor', 'AI', 'strategy'],
    details: 'This new capability creates pressure on roadmap differentiation and faster discovery.'
  }
];
