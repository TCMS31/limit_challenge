import { Suspense } from 'react';

import VehiclesPage from '@/components/vehicles-page';

export default function HomePage() {
  return (
    <Suspense>
      <VehiclesPage />
    </Suspense>
  );
}
