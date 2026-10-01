import { SubmissionPriority, SubmissionStatus } from '@/lib/types';

export const STATUS_LABELS: Record<SubmissionStatus, string> = {
  new: 'New',
  in_review: 'In Review',
  closed: 'Closed',
  lost: 'Lost',
};

export const PRIORITY_LABELS: Record<SubmissionPriority, string> = {
  high: 'High',
  medium: 'Medium',
  low: 'Low',
};

export function isStatus(value: string): value is SubmissionStatus {
  return value in STATUS_LABELS;
}

const DATE_FORMAT = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  timeZone: 'UTC',
});

const DATE_TIME_FORMAT = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
  timeZone: 'UTC',
  timeZoneName: 'short',
});

export function formatDate(value: string) {
  return DATE_FORMAT.format(new Date(value));
}

export function formatDateTime(value: string) {
  return DATE_TIME_FORMAT.format(new Date(value));
}

export function statusColor(status: SubmissionStatus): 'info' | 'warning' | 'success' | 'default' {
  if (status === 'new') return 'info';
  if (status === 'in_review') return 'warning';
  if (status === 'closed') return 'success';
  return 'default';
}

export function priorityColor(priority: SubmissionPriority): 'error' | 'warning' | 'default' {
  if (priority === 'high') return 'error';
  if (priority === 'medium') return 'warning';
  return 'default';
}
