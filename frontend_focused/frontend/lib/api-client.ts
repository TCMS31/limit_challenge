import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';

import { getSession, setSession } from '@/lib/auth-session';

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 15_000,
  withCredentials: true,
});

type RetryConfig = InternalAxiosRequestConfig & { _retry?: boolean };

export async function refreshAccess() {
  const { data } = await axios.post<{ access: string }>(
    `${apiBaseUrl}/auth/token/refresh/`,
    {},
    { withCredentials: true },
  );
  setSession({ access: data.access });
  return data.access;
}

apiClient.interceptors.request.use((config) => {
  const access = getSession()?.access;
  if (access) {
    config.headers.Authorization = `Bearer ${access}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetryConfig | undefined;
    const url = original?.url ?? '';
    const isAuthCall = url.includes('/auth/token/') || url.includes('/auth/logout/');
    if (error.response?.status !== 401 || !original || original._retry || isAuthCall) {
      return Promise.reject(error);
    }

    original._retry = true;
    try {
      const access = await refreshAccess();
      original.headers.Authorization = `Bearer ${access}`;
      return apiClient(original);
    } catch (refreshError) {
      setSession(null);
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.assign('/login');
      }
      return Promise.reject(refreshError);
    }
  },
);
