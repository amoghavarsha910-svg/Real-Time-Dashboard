import { Outlet } from 'react-router-dom';

/**
 * AppLayout — top-level shell for authenticated pages.
 * Sidebar and TopNav will be fully implemented in Phase 7.
 */
function Sidebar() {
  return (
    <aside className="w-64 shrink-0 border-r border-border bg-sidebar min-h-screen p-4">
      <p className="text-sidebar-foreground text-sm font-semibold">RTDD</p>
      {/* Navigation links — Phase 7 */}
    </aside>
  );
}

function TopNav() {
  return (
    <header className="h-14 border-b border-border bg-background flex items-center px-6">
      {/* Breadcrumb / actions — Phase 7 */}
    </header>
  );
}

export default function AppLayout() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopNav />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
