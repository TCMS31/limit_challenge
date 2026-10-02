'use client';

import { Alert, Box, Button, Paper, TextField, Typography } from '@mui/material';
import { useRouter } from 'next/navigation';
import { FormEvent, useState } from 'react';

import { apiClient } from '@/lib/api-client';
import { setSession } from '@/lib/auth-session';
import { formatApiError } from '@/lib/fleet-api';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError('');
    setPending(true);
    try {
      const { data } = await apiClient.post<{ access: string }>('/auth/token/', {
        username,
        password,
      });
      setSession({ access: data.access });
      router.replace('/');
    } catch (loginError) {
      setError(formatApiError(loginError));
    } finally {
      setPending(false);
    }
  }

  return (
    <Box display="flex" justifyContent="center" pt={8}>
      <Paper component="form" onSubmit={handleSubmit} sx={{ p: 4, width: '100%', maxWidth: 420, display: 'grid', gap: 2 }}>
        <Typography variant="h5" component="h1">
          Sign in
        </Typography>
        <Typography color="text.secondary">Use the demo account from the seed command.</Typography>
        {error ? <Alert severity="error">{error}</Alert> : null}
        <TextField label="Username" value={username} onChange={(event) => setUsername(event.target.value)} required />
        <TextField
          label="Password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
        <Button type="submit" variant="contained" disabled={pending}>
          {pending ? 'Signing in…' : 'Sign in'}
        </Button>
      </Paper>
    </Box>
  );
}
