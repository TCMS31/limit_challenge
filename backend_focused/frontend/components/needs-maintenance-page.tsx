'use client';

import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';

import { fetchNeedsMaintenance, fetchOffices, formatApiError } from '@/lib/fleet-api';

export default function NeedsMaintenancePage() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const page = searchParams.get('page') ?? '';
  const pageNumber = Number(page || '1');
  const vehicles = useQuery({
    queryKey: ['vehicles', 'needs-maintenance', page],
    queryFn: () => fetchNeedsMaintenance(page),
  });
  const offices = useQuery({ queryKey: ['offices'], queryFn: fetchOffices });
  const officeName = new Map((offices.data ?? []).map((office) => [office.id, office.name]));

  function goTo(nextPage: number) {
    const next = new URLSearchParams(searchParams.toString());
    if (nextPage <= 1) {
      next.delete('page');
    } else {
      next.set('page', String(nextPage));
    }
    const query = next.toString();
    router.replace(query ? `${pathname}?${query}` : pathname);
  }

  return (
    <Box display="flex" flexDirection="column" gap={3}>
      <Box>
        <Typography variant="h4" component="h1">
          Needs maintenance
        </Typography>
        <Typography color="text.secondary">
          Active vehicles that have never been serviced, or whose last service was more than a year ago.
        </Typography>
      </Box>
      {vehicles.isLoading ? (
        <Box display="flex" justifyContent="center" py={6}>
          <CircularProgress />
        </Box>
      ) : null}
      {vehicles.isError ? <Alert severity="error">{formatApiError(vehicles.error)}</Alert> : null}
      {vehicles.data && vehicles.data.results.length === 0 ? (
        <Alert severity="success">Every active vehicle has been serviced within the last year.</Alert>
      ) : null}
      {vehicles.data && vehicles.data.results.length > 0 ? (
        <Paper>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>VIN</TableCell>
                <TableCell>Vehicle</TableCell>
                <TableCell>Office</TableCell>
                <TableCell>Last maintenance</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {vehicles.data.results.map((vehicle) => (
                <TableRow key={vehicle.id} hover>
                  <TableCell>
                    <Link href={`/vehicles/${vehicle.id}`}>{vehicle.vin}</Link>
                  </TableCell>
                  <TableCell>
                    {vehicle.year} {vehicle.make} {vehicle.model}
                  </TableCell>
                  <TableCell>{officeName.get(vehicle.office) ?? vehicle.office}</TableCell>
                  <TableCell>{vehicle.last_maintenance ?? 'Never'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      ) : null}
      {vehicles.data && vehicles.data.count > vehicles.data.results.length ? (
        <Box display="flex" justifyContent="flex-end" gap={1}>
          <Button disabled={!vehicles.data.previous} onClick={() => goTo(pageNumber - 1)}>
            Previous
          </Button>
          <Button disabled={!vehicles.data.next} onClick={() => goTo(pageNumber + 1)}>
            Next
          </Button>
        </Box>
      ) : null}
    </Box>
  );
}
