'use client';

import { AppBar, Button, Toolbar, Typography } from '@mui/material';
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
    void restore();
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
      router.replace('/submissions');
    }
  }, [restored, session, isLogin, router]);

  if (!restored && !isLogin) {
    return null;
  }

  if (isLogin) {
    return children;
  }

  if (!session) {
    return null;
  }

  return (
    <>
      <AppBar
        position="static"
        color="inherit"
        elevation={0}
        sx={{ borderBottom: 1, borderColor: 'divider' }}
      >
        <Toolbar sx={{ gap: 1 }}>
          <Typography
            variant="h6"
            component={Link}
            href="/submissions"
            sx={{
              flexGrow: 1,
              fontWeight: 700,
              color: 'text.primary',
              textDecoration: 'none',
              transition: 'color 160ms ease',
              '&:hover': { color: 'primary.main' },
            }}
          >
            Submission Tracker
          </Typography>
          <Button
            component={Link}
            href="/submissions"
            color="inherit"
            sx={{
              borderRadius: 2,
              bgcolor: pathname.startsWith('/submissions') ? 'action.selected' : 'transparent',
              '&:hover': { bgcolor: 'action.hover' },
            }}
          >
            Submissions
          </Button>
          <Button
            color="inherit"
            sx={{ borderRadius: 2, '&:hover': { bgcolor: 'action.hover' } }}
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
      {children}
    </>
  );
}
