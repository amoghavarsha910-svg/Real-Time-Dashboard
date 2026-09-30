import { Outlet } from 'react-router-dom';

/**
 * AuthLayout — centred card wrapper for login / register / forgot-password pages.
 * Full styling will be applied in Phase 7.
 */
export default function AuthLayout() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        <div className="rounded-lg border border-border bg-card p-8 shadow-sm">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
