'use client';

import { AppBar, Button, Container, Toolbar, Typography } from '@mui/material';
import Link from 'next/link';
import { PropsWithChildren } from 'react';

export default function AppShell({ children }: PropsWithChildren) {
  return (
    <>
      <AppBar position="static" color="inherit" elevation={0} sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Toolbar sx={{ gap: 1 }}>
          <Typography variant="h6" component="p" sx={{ flexGrow: 1, fontWeight: 700 }}>
            Fleet Tracker
          </Typography>
          <Button component={Link} href="/" color="inherit">
            Vehicles
          </Button>
          <Button component={Link} href="/needs-maintenance" color="inherit">
            Needs maintenance
          </Button>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {children}
      </Container>
    </>
  );
}
