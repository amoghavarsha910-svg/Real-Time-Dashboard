import { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

import { ThemeProvider } from '@/context/ThemeContext';
import AppLayout from '@/layouts/AppLayout';
import AuthLayout from '@/layouts/AuthLayout';
import ProtectedRoute from '@/layouts/ProtectedRoute';
import { ROUTES } from '@/utils/constants';

// Auth pages
const LoginPage = lazy(() => import('@/pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/auth/RegisterPage'));
const ForgotPasswordPage = lazy(() => import('@/pages/auth/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('@/pages/auth/ResetPasswordPage'));

// App pages
const DashboardPage = lazy(() => import('@/pages/DashboardPage'));
const LiveDataPage = lazy(() => import('@/pages/LiveDataPage'));
const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage'));
const HistoricalDataPage = lazy(() => import('@/pages/HistoricalDataPage'));
const DataSourcesPage = lazy(() => import('@/pages/DataSourcesPage'));
const AlertsPage = lazy(() => import('@/pages/AlertsPage'));
const NotificationsPage = lazy(() => import('@/pages/NotificationsPage'));
const ReportsPage = lazy(() => import('@/pages/ReportsPage'));
const SettingsPage = lazy(() => import('@/pages/SettingsPage'));
const ProfilePage = lazy(() => import('@/pages/ProfilePage'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BrowserRouter>
          <Suspense
            fallback={
              <div className="flex min-h-screen items-center justify-center text-muted-foreground">
                Loading…
              </div>
            }
          >
            <Routes>
              {/* Root redirect */}
              <Route path="/" element={<Navigate to={ROUTES.DASHBOARD} replace />} />

              {/* Auth routes */}
              <Route element={<AuthLayout />}>
                <Route path={ROUTES.LOGIN} element={<LoginPage />} />
                <Route path={ROUTES.REGISTER} element={<RegisterPage />} />
                <Route path={ROUTES.FORGOT_PASSWORD} element={<ForgotPasswordPage />} />
                <Route path={ROUTES.RESET_PASSWORD} element={<ResetPasswordPage />} />
              </Route>

              {/* Protected app routes */}
              <Route element={<ProtectedRoute />}>
                <Route element={<AppLayout />}>
                  <Route path={ROUTES.DASHBOARD} element={<DashboardPage />} />
                  <Route path={ROUTES.LIVE_DATA} element={<LiveDataPage />} />
                  <Route path={ROUTES.ANALYTICS} element={<AnalyticsPage />} />
                  <Route path={ROUTES.HISTORY} element={<HistoricalDataPage />} />
                  <Route path={ROUTES.SOURCES} element={<DataSourcesPage />} />
                  <Route path={ROUTES.ALERTS} element={<AlertsPage />} />
                  <Route path={ROUTES.NOTIFICATIONS} element={<NotificationsPage />} />
                  <Route path={ROUTES.REPORTS} element={<ReportsPage />} />
                  <Route path={ROUTES.SETTINGS} element={<SettingsPage />} />
                  <Route path={ROUTES.PROFILE} element={<ProfilePage />} />
                </Route>
              </Route>
            </Routes>
          </Suspense>
        </BrowserRouter>
      </ThemeProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
