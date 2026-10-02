'use client';

import { AppBar, Button, Container, Toolbar, Typography } from '@mui/material';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { PropsWithChildren, useEffect, useState, useSyncExternalStore } from 'react';

import { apiClient, refreshAccess } from '@/lib/api-client';
import { getSession, setSession, subscribe } from '@/lib/auth-session';

export default function AppShell({ children }: PropsWithChildren) {
  const pathname = usePathname();
  const router = useRouter();
  const session = useSyncExternalStore(subscribe, getSession, () => null);
  const isLogin = pathname === '/login';
  const [restored, setRestored] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function restore() {
      if (!getSession()) {
        try {
          await refreshAccess();
        } catch {
          if (!cancelled) {
            setSession(null);
          }
        }
      }
      if (!cancelled) {
        setRestored(true);
      }
    }
    restore();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!restored) {
      return;
    }
    if (!session && !isLogin) {
      router.replace('/login');
    }
    if (session && isLogin) {
      router.replace('/');
    }
  }, [restored, session, isLogin, router]);

  if (!restored && !isLogin) {
    return null;
  }

  if (isLogin) {
    return <Container maxWidth="lg">{children}</Container>;
  }

  if (!session) {
    return null;
  }

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
          <Button
            color="inherit"
            onClick={() => {
              void apiClient.post('/auth/logout/').finally(() => {
                setSession(null);
                router.replace('/login');
              });
            }}
          >
            Sign out
          </Button>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        {children}
      </Container>
    </>
  );
}
