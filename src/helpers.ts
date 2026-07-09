import type { DataItem, SourceType } from './types';

export const sourceLabels: Record<SourceType, string> = {
  feedback: 'Customer Feedback',
  support: 'Support Cases',
  jira: 'Jira Tickets',
  usage: 'Usage Data',
  competitor: 'Competitor Notes'
};

export const sourceColors: Record<SourceType, string> = {
  feedback: '#2563eb',
  support: '#16a34a',
  jira: '#d97706',
  usage: '#8b5cf6',
  competitor: '#e11d48'
};

export function groupBySource(items: DataItem[]) {
  return items.reduce<Record<SourceType, DataItem[]>>((groups, item) => {
    groups[item.source] = groups[item.source] ?? [];
    groups[item.source].push(item);
    return groups;
  }, {
    feedback: [],
    support: [],
    jira: [],
    usage: [],
    competitor: []
  });
}

export function mapStrategyQuestion(question: string) {
  const lower = question.toLowerCase();
  if (lower.includes('priorit') || lower.includes('roadmap')) {
    return 'How should we prioritize features for the next quarter?';
  }
  if (lower.includes('churn') || lower.includes('retain')) {
    return 'What are the biggest retention risks and opportunities?';
  }
  if (lower.includes('competitor') || lower.includes('market')) {
    return 'How should we respond to competitor moves and market signals?';
  }
  return 'What strategic product themes should we focus on next?';
}
