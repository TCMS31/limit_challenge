'use client';

import { Card, CardContent, MenuItem, Stack, TextField } from '@mui/material';

import { Broker, SubmissionStatus } from '@/lib/types';

const STATUS_OPTIONS: { label: string; value: SubmissionStatus | '' }[] = [
  { label: 'All statuses', value: '' },
  { label: 'New', value: 'new' },
  { label: 'In Review', value: 'in_review' },
  { label: 'Closed', value: 'closed' },
  { label: 'Lost', value: 'lost' },
];

type SubmissionFiltersProps = {
  status: SubmissionStatus | '';
  brokerId: string;
  companyInput: string;
  brokers: Broker[] | undefined;
  brokersLoading: boolean;
  brokersError: boolean;
  onStatusChange: (status: string) => void;
  onBrokerChange: (brokerId: string) => void;
  onCompanyInputChange: (value: string) => void;
};

export default function SubmissionFilters({
  status,
  brokerId,
  companyInput,
  brokers,
  brokersLoading,
  brokersError,
  onStatusChange,
  onBrokerChange,
  onCompanyInputChange,
}: SubmissionFiltersProps) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <TextField
            select
            label="Status"
            value={status}
            onChange={(event) => onStatusChange(event.target.value)}
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
            onChange={(event) => onBrokerChange(event.target.value)}
            fullWidth
            disabled={brokersLoading}
            helperText={brokersError ? 'Brokers could not be loaded' : undefined}
            error={brokersError}
            slotProps={{
              inputLabel: { shrink: true },
              select: { displayEmpty: true },
            }}
          >
            <MenuItem value="">All brokers</MenuItem>
            {brokers?.map((broker) => (
              <MenuItem key={broker.id} value={String(broker.id)}>
                {broker.name}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            label="Company search"
            value={companyInput}
            onChange={(event) => onCompanyInputChange(event.target.value)}
            fullWidth
            placeholder="Acme, Health…"
            helperText="Matches the company name"
          />
        </Stack>
      </CardContent>
    </Card>
  );
}
