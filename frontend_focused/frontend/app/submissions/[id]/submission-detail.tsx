'use client';

import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Divider,
  Link as MuiLink,
  Skeleton,
  Stack,
  Typography,
} from '@mui/material';
import axios from 'axios';
import Link from 'next/link';
import { useParams, useSearchParams } from 'next/navigation';
import { Children, ReactNode } from 'react';

import { useSubmissionDetail } from '@/lib/hooks/useSubmissions';
import {
  PRIORITY_LABELS,
  STATUS_LABELS,
  formatDate,
  formatDateTime,
  priorityColor,
  statusColor,
} from '@/lib/submission-display';
import { SubmissionDetail as SubmissionDetailRecord } from '@/lib/types';

export default function SubmissionDetail() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const submissionId = params?.id ?? '';
  const listQuery = searchParams.toString();
  const listHref = listQuery ? `/submissions?${listQuery}` : '/submissions';
  const detailQuery = useSubmissionDetail(submissionId);
  const notFound =
    axios.isAxiosError(detailQuery.error) && detailQuery.error.response?.status === 404;

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 3, md: 5 } }}>
      <Stack spacing={2.5}>
        <Button
          component={Link}
          href={listHref}
          size="small"
          sx={{ alignSelf: 'flex-start', px: 0, textTransform: 'none' }}
        >
          ← Back to submissions
        </Button>

        {detailQuery.isLoading ? <DetailSkeleton /> : null}

        {detailQuery.isError && notFound ? (
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6">Submission not found</Typography>
              <Typography color="text.secondary" sx={{ mt: 0.5 }}>
                This record is not in the tracker. Return to the list and choose another one.
              </Typography>
            </CardContent>
          </Card>
        ) : null}

        {detailQuery.isError && !notFound ? (
          <Alert
            severity="error"
            action={
              <Button color="inherit" onClick={() => detailQuery.refetch()}>
                Retry
              </Button>
            }
          >
            This submission could not be loaded.
          </Alert>
        ) : null}

        {detailQuery.data ? <DetailBody submission={detailQuery.data} /> : null}
      </Stack>
    </Container>
  );
}

function DetailBody({ submission }: { submission: SubmissionDetailRecord }) {
  const location = [submission.company.industry, submission.company.headquartersCity]
    .filter(Boolean)
    .join(' · ');

  return (
    <Stack spacing={2.5}>
      <Card variant="outlined">
        <CardContent sx={{ p: { xs: 2, md: 3 }, '&:last-child': { pb: { xs: 2, md: 3 } } }}>
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            spacing={1.5}
            sx={{ justifyContent: 'space-between', alignItems: { sm: 'flex-start' } }}
          >
            <Box>
              <Typography variant="h4" component="h1">
                {submission.company.legalName}
              </Typography>
              {location ? (
                <Typography color="text.secondary" sx={{ mt: 0.5 }}>
                  {location}
                </Typography>
              ) : null}
            </Box>
            <Stack direction="row" spacing={1} sx={{ flexShrink: 0 }}>
              <Chip
                size="small"
                label={STATUS_LABELS[submission.status]}
                color={statusColor(submission.status)}
              />
              <Chip
                size="small"
                variant="outlined"
                label={`${PRIORITY_LABELS[submission.priority]} priority`}
                color={priorityColor(submission.priority)}
              />
            </Stack>
          </Stack>

          <Typography sx={{ mt: 2.5, maxWidth: 760 }}>
            {submission.summary || 'No summary was provided for this submission.'}
          </Typography>

          <Box
            sx={{
              mt: 2.5,
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: 'repeat(4, 1fr)' },
              gap: 1.5,
            }}
          >
            <Meta
              label="Broker"
              value={submission.broker.name}
              detail={submission.broker.primaryContactEmail}
            />
            <Meta label="Owner" value={submission.owner.fullName} detail={submission.owner.email} />
            <Meta label="Created" value={formatDateTime(submission.createdAt)} />
            <Meta label="Updated" value={formatDateTime(submission.updatedAt)} />
          </Box>
        </CardContent>
      </Card>

      <Section
        title="Contacts"
        count={submission.contacts.length}
        empty="No contacts on this submission."
      >
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
            gap: 1.5,
          }}
        >
          {submission.contacts.map((contact) => (
            <Box
              key={contact.id}
              sx={{
                border: 1,
                borderColor: 'divider',
                borderRadius: 1,
                p: 1.5,
              }}
            >
              <Typography fontWeight={600}>{contact.name}</Typography>
              <Typography variant="body2" color="text.secondary">
                {contact.role || 'Role not listed'}
              </Typography>
              <Stack spacing={0.25} sx={{ mt: 1 }}>
                {contact.email ? (
                  <MuiLink href={`mailto:${contact.email}`} variant="body2">
                    {contact.email}
                  </MuiLink>
                ) : null}
                {contact.phone ? (
                  <MuiLink href={`tel:${contact.phone}`} variant="body2" color="text.secondary">
                    {contact.phone}
                  </MuiLink>
                ) : null}
              </Stack>
            </Box>
          ))}
        </Box>
      </Section>

      <Section
        title="Documents"
        count={submission.documents.length}
        empty="No documents are attached."
      >
        <Stack divider={<Divider flexItem />} spacing={0}>
          {submission.documents.map((document) => (
            <Stack
              key={document.id}
              direction={{ xs: 'column', sm: 'row' }}
              spacing={1}
              sx={{ py: 1.5, alignItems: { sm: 'center' }, justifyContent: 'space-between' }}
            >
              <Box sx={{ minWidth: 0 }}>
                <Typography fontWeight={600}>{document.title}</Typography>
                <Stack direction="row" spacing={1} sx={{ mt: 0.5, alignItems: 'center' }}>
                  <Chip size="small" variant="outlined" label={document.docType} />
                  <Typography variant="body2" color="text.secondary">
                    {formatDate(document.uploadedAt)}
                  </Typography>
                </Stack>
              </Box>
              {document.fileUrl ? (
                <Button
                  component="a"
                  href={document.fileUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  size="small"
                  variant="outlined"
                  sx={{
                    alignSelf: { xs: 'flex-start', sm: 'center' },
                    flexShrink: 0,
                    textTransform: 'none',
                  }}
                >
                  Open file
                </Button>
              ) : null}
            </Stack>
          ))}
        </Stack>
      </Section>

      <Section title="Notes" count={submission.notes.length} empty="No notes have been added.">
        <Stack spacing={1.5}>
          {submission.notes.map((note) => (
            <Box
              key={note.id}
              sx={{
                borderLeft: 3,
                borderColor: 'primary.light',
                pl: 1.5,
                py: 0.5,
              }}
            >
              <Stack
                direction="row"
                spacing={1}
                sx={{ alignItems: 'baseline', justifyContent: 'space-between' }}
              >
                <Typography fontWeight={600}>{note.authorName}</Typography>
                <Typography variant="caption" color="text.secondary" sx={{ flexShrink: 0 }}>
                  {formatDateTime(note.createdAt)}
                </Typography>
              </Stack>
              <Typography sx={{ mt: 0.5 }}>{note.body}</Typography>
            </Box>
          ))}
        </Stack>
      </Section>
    </Stack>
  );
}

function Meta({ label, value, detail }: { label: string; value: string; detail?: string | null }) {
  return (
    <Box sx={{ bgcolor: 'action.hover', borderRadius: 1, px: 1.5, py: 1.25 }}>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography fontWeight={600}>{value}</Typography>
      {detail ? (
        <Typography variant="body2" color="text.secondary" sx={{ wordBreak: 'break-word' }}>
          {detail}
        </Typography>
      ) : null}
    </Box>
  );
}

function Section({
  title,
  count,
  empty,
  children,
}: {
  title: string;
  count: number;
  empty: string;
  children: ReactNode;
}) {
  const hasItems = Children.count(children) > 0 && count > 0;

  return (
    <Card variant="outlined">
      <CardContent sx={{ p: { xs: 2, md: 3 }, '&:last-child': { pb: { xs: 2, md: 3 } } }}>
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: hasItems ? 1.5 : 1 }}>
          <Typography variant="h6">{title}</Typography>
          <Chip size="small" label={count} />
        </Stack>
        {hasItems ? children : <Typography color="text.secondary">{empty}</Typography>}
      </CardContent>
    </Card>
  );
}

function DetailSkeleton() {
  return (
    <Stack spacing={2}>
      <Skeleton variant="rounded" height={220} />
      <Skeleton variant="rounded" height={140} />
      <Skeleton variant="rounded" height={140} />
      <Skeleton variant="rounded" height={140} />
    </Stack>
  );
}
