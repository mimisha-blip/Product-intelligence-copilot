export type SourceType = 'feedback' | 'support' | 'jira' | 'usage' | 'competitor';

export interface DataItem {
  id: string;
  source: SourceType;
  title: string;
  summary: string;
  createdAt: string;
  tags: string[];
  details?: string;
}
