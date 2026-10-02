import { apiClient } from '@/lib/api-client';
import { SubmissionListFilters } from '@/lib/types';

export async function downloadSubmissionsCsv(filters: Omit<SubmissionListFilters, 'page'>) {
  const params: Record<string, string> = {};
  if (filters.status) params.status = filters.status;
  if (filters.brokerId) params.brokerId = filters.brokerId;
  if (filters.companySearch) params.companySearch = filters.companySearch;

  const response = await apiClient.get<Blob>('/submissions/export/', {
    params,
    responseType: 'blob',
  });

  const url = URL.createObjectURL(response.data);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'submissions.csv';
  link.click();
  URL.revokeObjectURL(url);
}
