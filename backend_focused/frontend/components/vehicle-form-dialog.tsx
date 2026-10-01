'use client';

import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  MenuItem,
  Switch,
  TextField,
} from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { FormEvent, useEffect, useState } from 'react';

import { createVehicle, formatApiError, updateVehicle } from '@/lib/fleet-api';
import type { Office, Vehicle, VehicleInput } from '@/lib/types';

type VehicleFormDialogProps = {
  open: boolean;
  offices: Office[];
  vehicle?: Vehicle | null;
  onClose: () => void;
};

const emptyForm = {
  vin: '',
  license_plate: '',
  make: '',
  model: '',
  year: '2020',
  office: '',
  is_active: true,
};

export default function VehicleFormDialog({ open, offices, vehicle, onClose }: VehicleFormDialogProps) {
  const queryClient = useQueryClient();
  const [error, setError] = useState('');
  const [form, setForm] = useState(emptyForm);

  const mutation = useMutation({
    mutationFn: (input: VehicleInput) =>
      vehicle ? updateVehicle(vehicle.id, input) : createVehicle(input),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['vehicles'] });
      onClose();
    },
    onError: (mutationError) => setError(formatApiError(mutationError)),
  });

  useEffect(() => {
    if (!open) {
      return;
    }
    setError('');
    setForm(
      vehicle
        ? {
            vin: vehicle.vin,
            license_plate: vehicle.license_plate,
            make: vehicle.make,
            model: vehicle.model,
            year: String(vehicle.year),
            office: String(vehicle.office),
            is_active: vehicle.is_active,
          }
        : { ...emptyForm, office: offices[0] ? String(offices[0].id) : '' },
    );
  }, [open, vehicle, offices[0]?.id]);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError('');
    mutation.mutate({
      vin: form.vin.trim(),
      license_plate: form.license_plate.trim(),
      make: form.make.trim(),
      model: form.model.trim(),
      year: Number(form.year),
      office: Number(form.office),
      is_active: form.is_active,
    });
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <form onSubmit={handleSubmit}>
        <DialogTitle>{vehicle ? 'Edit vehicle' : 'Add vehicle'}</DialogTitle>
        <DialogContent sx={{ display: 'grid', gap: 2, pt: 1 }}>
          {error ? <Alert severity="error">{error}</Alert> : null}
          <TextField label="VIN" required value={form.vin} onChange={(event) => setForm({ ...form, vin: event.target.value })} />
          <TextField
            label="License plate"
            required
            value={form.license_plate}
            onChange={(event) => setForm({ ...form, license_plate: event.target.value })}
          />
          <TextField label="Make" required value={form.make} onChange={(event) => setForm({ ...form, make: event.target.value })} />
          <TextField label="Model" required value={form.model} onChange={(event) => setForm({ ...form, model: event.target.value })} />
          <TextField
            label="Year"
            required
            type="number"
            value={form.year}
            onChange={(event) => setForm({ ...form, year: event.target.value })}
          />
          <TextField
            select
            label="Office"
            required
            value={form.office}
            onChange={(event) => setForm({ ...form, office: event.target.value })}
          >
            {offices.map((office) => (
              <MenuItem key={office.id} value={String(office.id)}>
                {office.name} · {office.city}
              </MenuItem>
            ))}
          </TextField>
          <FormControlLabel
            control={
              <Switch checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} />
            }
            label="Active"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained" disabled={mutation.isPending}>
            {mutation.isPending ? 'Saving…' : 'Save'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
