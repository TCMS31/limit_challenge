'use client';

import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  Chip,
  Link as MuiLink,
  Pagination,
  Skeleton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

import {
  PRIORITY_LABELS,
  STATUS_LABELS,
  formatDate,
  priorityColor,
  statusColor,
} from '@/lib/submission-display';
import { SubmissionListItem } from '@/lib/types';

type SubmissionResultsProps = {
  submissions: SubmissionListItem[];
  page: number;
  pageCount: number;
  isFetching: boolean;
  detailHref: (id: number) => string;
  onPageChange: (page: number) => void;
};

export default function SubmissionResults({
  submissions,
  page,
  pageCount,
  isFetching,
  detailHref,
  onPageChange,
}: SubmissionResultsProps) {
  const router = useRouter();
  const currentPage = Math.min(page, pageCount);

  return (
    <Box
      sx={{
        opacity: isFetching ? 0.65 : 1,
        transition: 'opacity 180ms ease',
        '@keyframes rise': {
          from: { opacity: 0, transform: 'translateY(8px)' },
          to: { opacity: 1, transform: 'none' },
        },
        animation: 'rise 280ms ease',
        '@media (prefers-reduced-motion: reduce)': {
          animation: 'none',
          transition: 'none',
        },
      }}
    >
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
                  onClick={() => router.push(detailHref(submission.id))}
                  sx={{
                    cursor: 'pointer',
                    transition: 'background-color 160ms ease',
                    '&:hover .company-name': { color: 'primary.main' },
                    '&:hover .open-link': { transform: 'translateX(4px)' },
                  }}
                >
                  <TableCell sx={{ whiteSpace: 'nowrap' }}>
                    <Typography
                      className="company-name"
                      variant="body2"
                      fontWeight={600}
                      sx={{ transition: 'color 160ms ease' }}
                    >
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
                    <MuiLink
                      className="open-link"
                      component={Link}
                      href={detailHref(submission.id)}
                      underline="hover"
                      fontWeight={600}
                      onClick={(event) => event.stopPropagation()}
                      sx={{ display: 'inline-block', transition: 'transform 160ms ease' }}
                    >
                      Open
                    </MuiLink>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>

      <Stack spacing={2} sx={{ display: { xs: 'flex', md: 'none' } }}>
        {submissions.map((submission) => (
          <Card
            key={submission.id}
            variant="outlined"
            sx={{ '&:hover': { transform: 'translateY(-2px)', boxShadow: 3 } }}
          >
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
            page={currentPage}
            count={pageCount}
            onChange={(_event, nextPage) => onPageChange(nextPage)}
            color="primary"
            showFirstButton
            showLastButton
          />
          <Typography variant="caption" color="text.secondary">
            Page {currentPage} of {pageCount}
          </Typography>
        </Stack>
      ) : null}
    </Box>
  );
}

export function SubmissionSkeletons() {
  return (
    <Stack spacing={1}>
      {Array.from({ length: 6 }, (_, index) => (
        <Skeleton key={index} variant="rounded" height={52} />
      ))}
    </Stack>
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
