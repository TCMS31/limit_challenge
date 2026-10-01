'use client';

import { keepPreviousData, QueryKey, useQuery } from '@tanstack/react-query';
import axios from 'axios';

import { apiClient } from '@/lib/api-client';
import {
  PaginatedResponse,
  SubmissionDetail,
  SubmissionListFilters,
  SubmissionListItem,
} from '@/lib/types';

const SUBMISSIONS_QUERY_KEY = 'submissions';

async function fetchSubmissions(filters: SubmissionListFilters) {
  const params: Record<string, string | number> = {};
  if (filters.status) params.status = filters.status;
  if (filters.brokerId) params.brokerId = filters.brokerId;
  if (filters.companySearch) params.companySearch = filters.companySearch;
  if (filters.page && filters.page > 1) params.page = filters.page;

  const response = await apiClient.get<PaginatedResponse<SubmissionListItem>>('/submissions/', {
    params,
  });
  return response.data;
}

async function fetchSubmissionDetail(id: string | number) {
  if (!id) {
    throw new Error('Submission id is required');
  }

  const response = await apiClient.get<SubmissionDetail>(`/submissions/${id}/`);
  return response.data;
}

export function useSubmissionsList(filters: SubmissionListFilters) {
  return useQuery({
    queryKey: [SUBMISSIONS_QUERY_KEY, filters] as QueryKey,
    queryFn: () => fetchSubmissions(filters),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

export function useSubmissionDetail(id: string | number) {
  return useQuery({
    queryKey: [SUBMISSIONS_QUERY_KEY, 'detail', id],
    queryFn: () => fetchSubmissionDetail(id),
    enabled: Boolean(id),
    staleTime: 60_000,
    retry: (failureCount, error) => {
      if (axios.isAxiosError(error) && error.response?.status === 404) return false;
      return failureCount < 1;
    },
  });
}
