import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import UserSwitcher from './UserSwitcher';

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [switcherOpen, setSwitcherOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar open={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-14 border-b border-gray-200 bg-white flex items-center justify-between px-4 shrink-0">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 rounded-lg hover:bg-gray-100 transition"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <button
            onClick={() => setSwitcherOpen(!switcherOpen)}
            className="px-3 py-1.5 text-sm bg-gray-100 rounded-lg hover:bg-gray-200 transition"
          >
            Demo: Switch User
          </button>
        </header>
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
      {switcherOpen && <UserSwitcher onClose={() => setSwitcherOpen(false)} />}
    </div>
  );
}
