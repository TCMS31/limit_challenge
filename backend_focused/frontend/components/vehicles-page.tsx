'use client';

import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  MenuItem,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { FormEvent, useState } from 'react';

import { fetchOffices, formatApiError, searchVehicles } from '@/lib/fleet-api';
import type { Office } from '@/lib/types';
import VehicleFormDialog from './vehicle-form-dialog';

const filterKeys = ['office', 'active', 'make', 'model', 'maintained_after', 'maintained_before', 'certification_number'] as const;

export default function VehiclesPage() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [draft, setDraft] = useState({
    make: searchParams.get('make') ?? '',
    model: searchParams.get('model') ?? '',
    certification_number: searchParams.get('certification_number') ?? '',
  });

  const params = Object.fromEntries(searchParams.entries());
  const offices = useQuery({ queryKey: ['offices'], queryFn: fetchOffices });
  const vehicles = useQuery({
    queryKey: ['vehicles', 'search', params],
    queryFn: () => searchVehicles(params),
  });

  function writeParams(patch: Record<string, string | null>, resetPage = true) {
    const next = new URLSearchParams(searchParams.toString());
    for (const [key, value] of Object.entries(patch)) {
      if (!value) {
        next.delete(key);
      } else {
        next.set(key, value);
      }
    }
    if (resetPage) {
      next.delete('page');
    }
    const query = next.toString();
    router.replace(query ? `${pathname}?${query}` : pathname);
  }

  function applyTextFilters(event: FormEvent) {
    event.preventDefault();
    writeParams({
      make: draft.make.trim() || null,
      model: draft.model.trim() || null,
      certification_number: draft.certification_number.trim() || null,
    });
  }

  const officeName = new Map((offices.data ?? []).map((office) => [office.id, `${office.name}, ${office.city}`]));
  const page = Number(searchParams.get('page') ?? '1');

  return (
    <Box display="flex" flexDirection="column" gap={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" gap={2}>
        <Box>
          <Typography variant="h4" component="h1">
            Vehicles
          </Typography>
          <Typography color="text.secondary">Search the fleet and open a vehicle for its history.</Typography>
        </Box>
        <Button variant="contained" onClick={() => setDialogOpen(true)}>
          Add vehicle
        </Button>
      </Box>

      <Paper component="form" onSubmit={applyTextFilters} sx={{ p: 2, display: 'grid', gap: 2, gridTemplateColumns: { md: 'repeat(4, 1fr)' } }}>
        <TextField
          select
          label="Office"
          value={searchParams.get('office') ?? ''}
          onChange={(event) => writeParams({ office: event.target.value || null })}
        >
          <MenuItem value="">Any office</MenuItem>
          {(offices.data ?? []).map((office: Office) => (
            <MenuItem key={office.id} value={String(office.id)}>
              {office.name}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          label="Status"
          value={searchParams.get('active') ?? ''}
          onChange={(event) => writeParams({ active: event.target.value || null })}
        >
          <MenuItem value="">Any status</MenuItem>
          <MenuItem value="true">Active</MenuItem>
          <MenuItem value="false">Inactive</MenuItem>
        </TextField>
        <TextField label="Make" value={draft.make} onChange={(event) => setDraft({ ...draft, make: event.target.value })} />
        <TextField label="Model" value={draft.model} onChange={(event) => setDraft({ ...draft, model: event.target.value })} />
        <TextField
          label="Maintained after"
          type="date"
          slotProps={{ inputLabel: { shrink: true } }}
          value={searchParams.get('maintained_after') ?? ''}
          onChange={(event) => writeParams({ maintained_after: event.target.value || null })}
        />
        <TextField
          label="Maintained before"
          type="date"
          slotProps={{ inputLabel: { shrink: true } }}
          value={searchParams.get('maintained_before') ?? ''}
          onChange={(event) => writeParams({ maintained_before: event.target.value || null })}
        />
        <TextField
          label="Mechanic certification"
          value={draft.certification_number}
          onChange={(event) => setDraft({ ...draft, certification_number: event.target.value })}
        />
        <Box display="flex" gap={1} alignItems="center">
          <Button type="submit" variant="outlined">
            Apply
          </Button>
          <Button
            type="button"
            onClick={() => {
              setDraft({ make: '', model: '', certification_number: '' });
              const next = new URLSearchParams(searchParams.toString());
              filterKeys.forEach((key) => next.delete(key));
              next.delete('page');
              const query = next.toString();
              router.replace(query ? `${pathname}?${query}` : pathname);
            }}
          >
            Clear
          </Button>
        </Box>
      </Paper>

      {vehicles.isLoading ? (
        <Box display="flex" justifyContent="center" py={6}>
          <CircularProgress />
        </Box>
      ) : null}
      {vehicles.isError ? <Alert severity="error">{formatApiError(vehicles.error)}</Alert> : null}
      {vehicles.data && vehicles.data.results.length === 0 ? (
        <Alert severity="info">No vehicles match these filters.</Alert>
      ) : null}
      {vehicles.data && vehicles.data.results.length > 0 ? (
        <Paper>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>VIN</TableCell>
                <TableCell>Plate</TableCell>
                <TableCell>Vehicle</TableCell>
                <TableCell>Office</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {vehicles.data.results.map((vehicle) => (
                <TableRow key={vehicle.id} hover>
                  <TableCell>
                    <Link href={`/vehicles/${vehicle.id}`}>{vehicle.vin}</Link>
                  </TableCell>
                  <TableCell>{vehicle.license_plate}</TableCell>
                  <TableCell>
                    {vehicle.year} {vehicle.make} {vehicle.model}
                  </TableCell>
                  <TableCell>{officeName.get(vehicle.office) ?? vehicle.office}</TableCell>
                  <TableCell>
                    <Chip size="small" label={vehicle.is_active ? 'Active' : 'Inactive'} color={vehicle.is_active ? 'success' : 'default'} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      ) : null}
      {vehicles.data && vehicles.data.count > vehicles.data.results.length ? (
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography color="text.secondary">{vehicles.data.count} vehicles</Typography>
          <Box display="flex" gap={1}>
            <Button disabled={!vehicles.data.previous} onClick={() => writeParams({ page: String(page - 1) }, false)}>
              Previous
            </Button>
            <Button disabled={!vehicles.data.next} onClick={() => writeParams({ page: String(page + 1) }, false)}>
              Next
            </Button>
          </Box>
        </Box>
      ) : null}

      <VehicleFormDialog open={dialogOpen} offices={offices.data ?? []} onClose={() => setDialogOpen(false)} />
    </Box>
  );
}
