import axios from 'axios';

import { apiClient } from './api-client';
import type { Office, Page, Vehicle, VehicleDetail, VehicleInput } from './types';

export function formatApiError(error: unknown) {
  if (!axios.isAxiosError(error)) {
    return 'Something went wrong. Try again.';
  }
  const data = error.response?.data;
  if (!data || typeof data !== 'object') {
    return error.message || 'Something went wrong. Try again.';
  }
  return Object.entries(data as Record<string, unknown>)
    .map(([field, value]) => {
      const message = Array.isArray(value) ? value.join(' ') : String(value);
      return field === 'detail' ? message : `${field}: ${message}`;
    })
    .join(' ');
}

export async function fetchOffices() {
  const { data } = await apiClient.get<Page<Office>>('/offices/');
  return data.results;
}

export async function searchVehicles(params: Record<string, string>) {
  const { data } = await apiClient.get<Page<Vehicle>>('/vehicles/search/', { params });
  return data;
}

export async function fetchNeedsMaintenance(page: string) {
  const { data } = await apiClient.get<Page<Vehicle>>('/vehicles/needs-maintenance/', {
    params: page ? { page } : undefined,
  });
  return data;
}

export async function fetchVehicle(id: string) {
  const { data } = await apiClient.get<VehicleDetail>(`/vehicles/${id}/`);
  return data;
}

export async function createVehicle(input: VehicleInput) {
  const { data } = await apiClient.post<Vehicle>('/vehicles/', input);
  return data;
}

export async function updateVehicle(id: number, input: VehicleInput) {
  const { data } = await apiClient.put<Vehicle>(`/vehicles/${id}/`, input);
  return data;
}

export async function assignVehicle(id: number, office: number) {
  const { data } = await apiClient.post<Vehicle>(`/vehicles/${id}/assign/`, { office });
  return data;
}
