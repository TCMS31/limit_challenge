'use client';

import {
  Alert,
  Box,
  Button,
  IconButton,
  InputAdornment,
  Paper,
  TextField,
  Typography,
} from '@mui/material';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import { FormEvent, useState } from 'react';

import { EyeIcon, EyeOffIcon } from '@/components/password-visibility-icons';
import { apiClient } from '@/lib/api-client';
import { setSession } from '@/lib/auth-session';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

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
      router.replace('/submissions');
    } catch (loginError) {
      const detail = axios.isAxiosError(loginError) ? loginError.response?.data?.detail : null;
      setError(
        typeof detail === 'string' ? detail : 'Sign in failed. Check the username and password.',
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <Box display="flex" justifyContent="center" pt={8}>
      <Paper
        component="form"
        onSubmit={handleSubmit}
        sx={{ p: 4, width: '100%', maxWidth: 420, display: 'grid', gap: 2 }}
      >
        <Typography variant="h5" component="h1">
          Sign in
        </Typography>
        <Typography color="text.secondary">
          Use submission / submission-demo from the seed.
        </Typography>
        {error ? <Alert severity="error">{error}</Alert> : null}
        <TextField
          label="Username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          required
        />
        <TextField
          label="Password"
          type={showPassword ? 'text' : 'password'}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
          slotProps={{
            input: {
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    onClick={() => setShowPassword((visible) => !visible)}
                    edge="end"
                  >
                    {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                  </IconButton>
                </InputAdornment>
              ),
            },
          }}
        />
        <Button type="submit" variant="contained" disabled={pending}>
          {pending ? 'Signing in…' : 'Sign in'}
        </Button>
      </Paper>
    </Box>
  );
}
