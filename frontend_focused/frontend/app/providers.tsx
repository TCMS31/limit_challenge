'use client';

import { AppRouterCacheProvider } from '@mui/material-nextjs/v16-appRouter';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import { PropsWithChildren, useMemo, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import AppShell from '@/components/app-shell';

function useTheme() {
  return useMemo(
    () =>
      createTheme({
        palette: {
          primary: {
            main: '#0f62fe',
          },
          background: {
            default: '#f5f7fb',
          },
        },
        shape: { borderRadius: 8 },
        components: {
          MuiButton: {
            styleOverrides: {
              root: {
                textTransform: 'none',
                fontWeight: 600,
                transition:
                  'background-color 160ms ease, box-shadow 160ms ease, transform 160ms ease',
                '@media (prefers-reduced-motion: reduce)': {
                  transition: 'none',
                },
              },
              outlined: {
                '&:hover': {
                  transform: 'translateY(-1px)',
                  boxShadow: '0 4px 12px rgba(15, 98, 254, 0.12)',
                },
              },
            },
          },
          MuiCard: {
            styleOverrides: {
              root: {
                transition: 'box-shadow 180ms ease, border-color 180ms ease, transform 180ms ease',
                '@media (prefers-reduced-motion: reduce)': {
                  transition: 'none',
                },
              },
            },
          },
        },
      }),
    [],
  );
}

export default function Providers({ children }: PropsWithChildren) {
  const theme = useTheme();
  const [queryClient] = useState(() => new QueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <AppRouterCacheProvider>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <AppShell>{children}</AppShell>
        </ThemeProvider>
      </AppRouterCacheProvider>
    </QueryClientProvider>
  );
}
