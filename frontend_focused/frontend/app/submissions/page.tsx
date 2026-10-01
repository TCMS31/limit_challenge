import { Skeleton, Stack } from '@mui/material';
import { Suspense } from 'react';

import SubmissionsWorkspace from './submissions-workspace';

export default function SubmissionsPage() {
  return (
    <Suspense
      fallback={
        <Stack spacing={1} sx={{ maxWidth: 960, mx: 'auto', py: 6, px: 2 }}>
          <Skeleton variant="rounded" height={72} />
          <Skeleton variant="rounded" height={280} />
        </Stack>
      }
    >
      <SubmissionsWorkspace />
    </Suspense>
  );
}
