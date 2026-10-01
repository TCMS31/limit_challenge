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
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { useState } from 'react';

import { assignVehicle, fetchOffices, fetchVehicle, formatApiError } from '@/lib/fleet-api';
import VehicleFormDialog from './vehicle-form-dialog';

export default function VehicleDetail({ id }: { id: string }) {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [officeId, setOfficeId] = useState('');
  const vehicle = useQuery({ queryKey: ['vehicles', id], queryFn: () => fetchVehicle(id) });
  const offices = useQuery({ queryKey: ['offices'], queryFn: fetchOffices });
  const assign = useMutation({
    mutationFn: (office: number) => assignVehicle(Number(id), office),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['vehicles', id] });
      await queryClient.invalidateQueries({ queryKey: ['vehicles', 'search'] });
    },
  });

  if (vehicle.isLoading) {
    return (
      <Box display="flex" justifyContent="center" py={8}>
        <CircularProgress />
      </Box>
    );
  }
  if (vehicle.isError || !vehicle.data) {
    return <Alert severity="error">{formatApiError(vehicle.error)}</Alert>;
  }

  const current = vehicle.data;
  const selectedOffice = officeId || String(current.office.id);

  return (
    <Box display="flex" flexDirection="column" gap={3}>
      <Button component={Link} href="/" sx={{ alignSelf: 'flex-start' }}>
        Back to vehicles
      </Button>
      <Box display="flex" justifyContent="space-between" gap={2} flexWrap="wrap">
        <Box>
          <Typography variant="h4" component="h1">
            {current.year} {current.make} {current.model}
          </Typography>
          <Typography color="text.secondary">
            VIN {current.vin} · Plate {current.license_plate}
          </Typography>
        </Box>
        <Box display="flex" gap={1} alignItems="center">
          <Chip label={current.is_active ? 'Active' : 'Inactive'} color={current.is_active ? 'success' : 'default'} />
          <Button variant="outlined" onClick={() => setEditing(true)}>
            Edit
          </Button>
        </Box>
      </Box>

      <Paper sx={{ p: 2, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <Typography>
          Office: {current.office.name}, {current.office.city}
        </Typography>
        <TextField
          select
          label="Move to"
          size="small"
          value={selectedOffice}
          onChange={(event) => setOfficeId(event.target.value)}
          sx={{ minWidth: 220 }}
        >
          {(offices.data ?? []).map((office) => (
            <MenuItem key={office.id} value={String(office.id)}>
              {office.name}
            </MenuItem>
          ))}
        </TextField>
        <Button
          variant="contained"
          disabled={assign.isPending || Number(selectedOffice) === current.office.id}
          onClick={() => assign.mutate(Number(selectedOffice))}
        >
          Assign
        </Button>
        {assign.isError ? <Alert severity="error">{formatApiError(assign.error)}</Alert> : null}
      </Paper>

      <Typography variant="h6" component="h2">
        Maintenance history
      </Typography>
      {current.maintenance_records.length === 0 ? <Alert severity="info">This vehicle has no maintenance records.</Alert> : null}
      {current.maintenance_records.length > 0 ? (
        <Paper>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Mechanic</TableCell>
                <TableCell>Cost</TableCell>
                <TableCell>Notes</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {current.maintenance_records.map((record) => (
                <TableRow key={record.id}>
                  <TableCell>{record.maintenance_date}</TableCell>
                  <TableCell>{record.maintenance_type.replaceAll('_', ' ')}</TableCell>
                  <TableCell>
                    {record.mechanic.name} · {record.mechanic.certification_number}
                  </TableCell>
                  <TableCell>${record.cost}</TableCell>
                  <TableCell>{record.notes}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      ) : null}

      <VehicleFormDialog
        open={editing}
        offices={offices.data ?? [current.office]}
        vehicle={{ ...current, office: current.office.id }}
        onClose={() => {
          setEditing(false);
          void queryClient.invalidateQueries({ queryKey: ['vehicles', id] });
        }}
      />
    </Box>
  );
}
