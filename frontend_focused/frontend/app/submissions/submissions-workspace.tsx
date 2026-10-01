'use client';

import {
  Alert,
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
  Chip,
  MenuItem,
  Container,
  Pagination,
  Skeleton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';

import { useBrokerOptions } from '@/lib/hooks/useBrokerOptions';
import { useSubmissionsList } from '@/lib/hooks/useSubmissions';
import { SubmissionListItem, SubmissionPriority, SubmissionStatus } from '@/lib/types';

const PAGE_SIZE = 10;

const STATUS_OPTIONS: { label: string; value: SubmissionStatus | '' }[] = [
  { label: 'All statuses', value: '' },
  { label: 'New', value: 'new' },
  { label: 'In Review', value: 'in_review' },
  { label: 'Closed', value: 'closed' },
  { label: 'Lost', value: 'lost' },
];

const STATUS_LABELS: Record<SubmissionStatus, string> = {
  new: 'New',
  in_review: 'In Review',
  closed: 'Closed',
  lost: 'Lost',
};

const PRIORITY_LABELS: Record<SubmissionPriority, string> = {
  high: 'High',
  medium: 'Medium',
  low: 'Low',
};

function isStatus(value: string): value is SubmissionStatus {
  return value in STATUS_LABELS;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric' }).format(
    new Date(value),
  );
}

function statusColor(status: SubmissionStatus): 'info' | 'warning' | 'success' | 'default' {
  if (status === 'new') return 'info';
  if (status === 'in_review') return 'warning';
  if (status === 'closed') return 'success';
  return 'default';
}

function priorityColor(priority: SubmissionPriority): 'error' | 'warning' | 'default' {
  if (priority === 'high') return 'error';
  if (priority === 'medium') return 'warning';
  return 'default';
}

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

        <Card variant="outlined">
          <CardContent>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <TextField
                select
                label="Status"
                value={status}
                onChange={(event) =>
                  replaceParams({ status: event.target.value || undefined }, true)
                }
                fullWidth
                slotProps={{
                  inputLabel: { shrink: true },
                  select: { displayEmpty: true },
                }}
              >
                {STATUS_OPTIONS.map((option) => (
                  <MenuItem key={option.value || 'all'} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                select
                label="Broker"
                value={brokerId}
                onChange={(event) =>
                  replaceParams({ brokerId: event.target.value || undefined }, true)
                }
                fullWidth
                disabled={brokerQuery.isLoading}
                helperText={brokerQuery.isError ? 'Brokers could not be loaded' : undefined}
                error={brokerQuery.isError}
                slotProps={{
                  inputLabel: { shrink: true },
                  select: { displayEmpty: true },
                }}
              >
                <MenuItem value="">All brokers</MenuItem>
                {brokerQuery.data?.map((broker) => (
                  <MenuItem key={broker.id} value={String(broker.id)}>
                    {broker.name}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                label="Company search"
                value={companyInput}
                onChange={(event) => setCompanyInput(event.target.value)}
                fullWidth
                placeholder="Acme, Health…"
                helperText="Matches the company name"
              />
            </Stack>
          </CardContent>
        </Card>

        <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between">
          <Typography color="text.secondary">
            {submissionsQuery.isLoading
              ? 'Loading submissions…'
              : total === 0
                ? '0 submissions'
                : `Showing ${(page - 1) * PAGE_SIZE + 1}–${Math.min(page * PAGE_SIZE, total)} of ${total}`}
          </Typography>
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
          <Box sx={{ opacity: submissionsQuery.isFetching ? 0.65 : 1 }}>
            <Box sx={{ display: { xs: 'none', md: 'block' } }}>
              <TableContainer component={Card} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Company</TableCell>
                      <TableCell>Broker</TableCell>
                      <TableCell>Owner</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Priority</TableCell>
                      <TableCell align="right">Docs</TableCell>
                      <TableCell align="right">Notes</TableCell>
                      <TableCell>Latest note</TableCell>
                      <TableCell>Created</TableCell>
                      <TableCell />
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {submissions.map((submission) => (
                      <TableRow
                        key={submission.id}
                        hover
                        component={Link}
                        href={detailHref(submission.id)}
                        sx={{ textDecoration: 'none', cursor: 'pointer' }}
                      >
                        <TableCell sx={{ whiteSpace: 'nowrap' }}>
                          <Typography variant="body2" fontWeight={600}>
                            {submission.company.legalName}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {submission.company.industry}
                          </Typography>
                        </TableCell>
                        <TableCell>{submission.broker.name}</TableCell>
                        <TableCell>{submission.owner.fullName}</TableCell>
                        <TableCell>
                          <Chip
                            size="small"
                            label={STATUS_LABELS[submission.status]}
                            color={statusColor(submission.status)}
                          />
                        </TableCell>
                        <TableCell>
                          <Chip
                            size="small"
                            variant="outlined"
                            label={PRIORITY_LABELS[submission.priority]}
                            color={priorityColor(submission.priority)}
                          />
                        </TableCell>
                        <TableCell align="right">{submission.documentCount}</TableCell>
                        <TableCell align="right">{submission.noteCount}</TableCell>
                        <TableCell sx={{ maxWidth: 240 }}>
                          <LatestNote note={submission.latestNote} />
                        </TableCell>
                        <TableCell sx={{ whiteSpace: 'nowrap' }}>
                          {formatDate(submission.createdAt)}
                        </TableCell>
                        <TableCell sx={{ whiteSpace: 'nowrap' }}>
                          <Typography variant="body2" color="primary" fontWeight={600}>
                            Open
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>

            <Stack spacing={2} sx={{ display: { xs: 'flex', md: 'none' } }}>
              {submissions.map((submission) => (
                <Card key={submission.id} variant="outlined">
                  <CardActionArea component={Link} href={detailHref(submission.id)}>
                    <CardContent>
                      <SubmissionCard submission={submission} />
                    </CardContent>
                  </CardActionArea>
                </Card>
              ))}
            </Stack>

            {pageCount > 1 ? (
              <Stack spacing={1} alignItems="center" sx={{ pt: 1 }}>
                <Pagination
                  page={Math.min(page, pageCount)}
                  count={pageCount}
                  onChange={(_event, nextPage) =>
                    replaceParams({ page: nextPage > 1 ? String(nextPage) : undefined })
                  }
                  color="primary"
                  showFirstButton
                  showLastButton
                />
                <Typography variant="caption" color="text.secondary">
                  Page {Math.min(page, pageCount)} of {pageCount}
                </Typography>
              </Stack>
            ) : null}
          </Box>
        ) : null}
      </Stack>
    </Container>
  );
}

function LatestNote({ note }: { note: SubmissionListItem['latestNote'] }) {
  if (!note) {
    return (
      <Typography variant="body2" color="text.secondary">
        No notes
      </Typography>
    );
  }

  return (
    <Box>
      <Typography variant="body2" noWrap title={note.bodyPreview}>
        {note.bodyPreview}
      </Typography>
      <Typography variant="caption" color="text.secondary">
        {note.authorName}
      </Typography>
    </Box>
  );
}

function SubmissionCard({ submission }: { submission: SubmissionListItem }) {
  return (
    <Stack spacing={1}>
      <Typography variant="subtitle1" fontWeight={600}>
        {submission.company.legalName}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {submission.broker.name} · {submission.owner.fullName}
      </Typography>
      <Stack direction="row" spacing={1}>
        <Chip
          size="small"
          label={STATUS_LABELS[submission.status]}
          color={statusColor(submission.status)}
        />
        <Chip
          size="small"
          variant="outlined"
          label={PRIORITY_LABELS[submission.priority]}
          color={priorityColor(submission.priority)}
        />
      </Stack>
      <Typography variant="body2">
        {submission.documentCount} documents · {submission.noteCount} notes
      </Typography>
      <LatestNote note={submission.latestNote} />
    </Stack>
  );
}

function SubmissionSkeletons() {
  return (
    <Stack spacing={1}>
      {Array.from({ length: 6 }, (_, index) => (
        <Skeleton key={index} variant="rounded" height={52} />
      ))}
    </Stack>
  );
}
