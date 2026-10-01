import { Suspense } from 'react';

import NeedsMaintenancePage from '@/components/needs-maintenance-page';

export default function NeedsMaintenanceRoute() {
  return (
    <Suspense>
      <NeedsMaintenancePage />
    </Suspense>
  );
}
