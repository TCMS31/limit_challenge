'use client';

import { Alert, Box, Button, Card, CardContent, Container, Stack, Typography } from '@mui/material';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';

import { downloadSubmissionsCsv } from '@/lib/export-submissions';
import { useBrokerOptions } from '@/lib/hooks/useBrokerOptions';
import { useSubmissionsList } from '@/lib/hooks/useSubmissions';
import { isStatus } from '@/lib/submission-display';
import { SubmissionStatus } from '@/lib/types';

import SubmissionFilters from './submission-filters';
import SubmissionResults, { SubmissionSkeletons } from './submission-results';

const PAGE_SIZE = 10;

export default function SubmissionsWorkspace() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const rawStatus = searchParams.get('status') ?? '';
  const status: SubmissionStatus | '' = isStatus(rawStatus) ? rawStatus : '';
  const brokerId = searchParams.get('brokerId') ?? '';
  const companySearch = searchParams.get('companySearch') ?? '';
  const page = Math.max(1, Number(searchParams.get('page') ?? '1') || 1);

  const [companyInput, setCompanyInput] = useState(companySearch);
  const [exporting, setExporting] = useState(false);
  const [trackedSearch, setTrackedSearch] = useState(companySearch);
  if (companySearch !== trackedSearch) {
    setTrackedSearch(companySearch);
    setCompanyInput(companySearch);
  }

  useEffect(() => {
    const trimmed = companyInput.trim();
    if (trimmed === companySearch) return;

    const timer = window.setTimeout(() => {
      const params = new URLSearchParams(searchParams.toString());
      if (trimmed) params.set('companySearch', trimmed);
      else params.delete('companySearch');
      params.delete('page');
      const query = params.toString();
      router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
    }, 300);

    return () => window.clearTimeout(timer);
  }, [companyInput, companySearch, pathname, router, searchParams]);

  const filters = useMemo(
    () => ({
      status: status || undefined,
      brokerId: brokerId || undefined,
      companySearch: companySearch || undefined,
      page,
    }),
    [status, brokerId, companySearch, page],
  );

  const submissionsQuery = useSubmissionsList(filters);
  const brokerQuery = useBrokerOptions();
  const submissions = submissionsQuery.data?.results ?? [];
  const total = submissionsQuery.data?.count ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const listQuery = searchParams.toString();
  const hasFilters = Boolean(status || brokerId || companySearch);

  function replaceParams(updates: Record<string, string | undefined>, resetPage = false) {
    const params = new URLSearchParams(searchParams.toString());
    for (const [key, value] of Object.entries(updates)) {
      if (value) params.set(key, value);
      else params.delete(key);
    }
    if (resetPage) params.delete('page');
    const query = params.toString();
    router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
  }

  function detailHref(id: number) {
    return listQuery ? `/submissions/${id}?${listQuery}` : `/submissions/${id}`;
  }

  const rangeLabel = submissionsQuery.isLoading
    ? 'Loading submissions…'
    : total === 0
      ? '0 submissions'
      : `Showing ${(page - 1) * PAGE_SIZE + 1}–${Math.min(page * PAGE_SIZE, total)} of ${total}`;

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      <Stack spacing={3}>
        <Box>
          <Typography variant="h4" component="h1">
            Submissions
          </Typography>
          <Typography color="text.secondary">
            Filter by status, broker, or company, then open a row to see contacts, documents, and
            notes.
          </Typography>
        </Box>

        <SubmissionFilters
          status={status}
          brokerId={brokerId}
          companyInput={companyInput}
          brokers={brokerQuery.data}
          brokersLoading={brokerQuery.isLoading}
          brokersError={brokerQuery.isError}
          onStatusChange={(nextStatus) => replaceParams({ status: nextStatus || undefined }, true)}
          onBrokerChange={(nextBrokerId) =>
            replaceParams({ brokerId: nextBrokerId || undefined }, true)
          }
          onCompanyInputChange={setCompanyInput}
        />

        <Stack direction="row" spacing={2} alignItems="center" justifyContent="flex-end">
          {submissionsQuery.isLoading ? (
            <Typography color="text.secondary" sx={{ mr: 'auto' }}>
              Loading submissions…
            </Typography>
          ) : null}
          <Button
            variant="outlined"
            disabled={exporting || submissionsQuery.isLoading || total === 0}
            onClick={() => {
              setExporting(true);
              void downloadSubmissionsCsv({
                status: status || undefined,
                brokerId: brokerId || undefined,
                companySearch: companySearch || undefined,
              }).finally(() => setExporting(false));
            }}
          >
            {exporting ? 'Exporting…' : 'Export CSV'}
          </Button>
          {hasFilters ? (
            <Button
              onClick={() => {
                setTrackedSearch('');
                setCompanyInput('');
                router.replace(pathname, { scroll: false });
              }}
            >
              Clear filters
            </Button>
          ) : null}
        </Stack>

        {submissionsQuery.isError ? (
          <Alert
            severity="error"
            action={
              <Button color="inherit" onClick={() => submissionsQuery.refetch()}>
                Retry
              </Button>
            }
          >
            Submissions could not be loaded.
          </Alert>
        ) : null}

        {submissionsQuery.isLoading ? <SubmissionSkeletons /> : null}

        {submissionsQuery.isSuccess && submissions.length === 0 ? (
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6">No matching submissions</Typography>
              <Typography color="text.secondary">
                Nothing matches these filters. Clear them to see the full list.
              </Typography>
            </CardContent>
          </Card>
        ) : null}

        {submissions.length > 0 ? (
          <SubmissionResults
            submissions={submissions}
            page={page}
            pageCount={pageCount}
            isFetching={submissionsQuery.isFetching}
            detailHref={detailHref}
            onPageChange={(nextPage) =>
              replaceParams({ page: nextPage > 1 ? String(nextPage) : undefined })
            }
          />
        ) : null}

        {submissionsQuery.isSuccess && total > 0 ? (
          <Typography color="text.secondary" textAlign="right">
            {rangeLabel}
          </Typography>
        ) : null}
      </Stack>
    </Container>
  );
}
