export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/live';

export const ROUTES = {
  DASHBOARD: '/dashboard',
  LIVE_DATA: '/live-data',
  ANALYTICS: '/analytics',
  HISTORY: '/history',
  SOURCES: '/sources',
  ALERTS: '/alerts',
  NOTIFICATIONS: '/notifications',
  REPORTS: '/reports',
  SETTINGS: '/settings',
  PROFILE: '/profile',
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  FORGOT_PASSWORD: '/auth/forgot-password',
  RESET_PASSWORD: '/auth/reset-password',
} as const;

export const TIME_RANGES = [
  { label: '5 minutes', value: '5m' },
  { label: '15 minutes', value: '15m' },
  { label: '1 hour', value: '1h' },
  { label: 'Today', value: 'today' },
  { label: 'Yesterday', value: 'yesterday' },
  { label: '7 days', value: '7d' },
  { label: '30 days', value: '30d' },
] as const;

export const SIMULATOR_INTERVALS = [
  { label: '500ms', value: 0.5 },
  { label: '1s', value: 1 },
  { label: '2s', value: 2 },
  { label: '5s', value: 5 },
  { label: '10s', value: 10 },
] as const;
