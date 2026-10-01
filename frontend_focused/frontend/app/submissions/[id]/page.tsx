import { Suspense } from 'react';

import SubmissionDetail from './submission-detail';

export default function SubmissionDetailPage() {
  return (
    <Suspense>
      <SubmissionDetail />
    </Suspense>
  );
}
