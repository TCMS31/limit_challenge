export type Page<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type Office = {
  id: number;
  name: string;
  city: string;
};

export type Vehicle = {
  id: number;
  vin: string;
  license_plate: string;
  make: string;
  model: string;
  year: number;
  office: number;
  is_active: boolean;
  last_maintenance?: string | null;
};

export type Mechanic = {
  id: number;
  name: string;
  certification_number: string;
  is_active: boolean;
};

export type MaintenanceRecord = {
  id: number;
  maintenance_date: string;
  maintenance_type: string;
  cost: string;
  notes: string;
  mechanic: Mechanic;
};

export type VehicleDetail = Omit<Vehicle, 'office' | 'last_maintenance'> & {
  office: Office;
  maintenance_records: MaintenanceRecord[];
};

export type VehicleInput = {
  vin: string;
  license_plate: string;
  make: string;
  model: string;
  year: number;
  office: number;
  is_active: boolean;
};
