import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { useToastStore } from '@/store/toastStore';
import api from '@/services/api';
import NotificationCenter from '@/components/layout/NotificationCenter';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  LayoutDashboard,
  Building2,
  Briefcase,
  Users,
  CalendarCheck,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
  User as UserIcon,
  Shield,
  Menu,
  Server,
  Activity,
  ShieldCheck
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavItem {
  name: string;
  path: string;
  icon: React.ComponentType<any>;
}

const navItems: NavItem[] = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Organizations', path: '/organizations', icon: Building2 },
  { name: 'Departments', path: '/departments', icon: Briefcase },
  { name: 'Members', path: '/members', icon: Users },
  { name: 'Attendance', path: '/attendance', icon: CalendarCheck },
  { name: 'Evidence', path: '/evidence', icon: ShieldCheck },
  { name: 'Reports', path: '/reports', icon: FileText },
  { name: 'Settings', path: '/settings', icon: Settings },
];

export default function AppLayout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const [systemStatus, setSystemStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [systemVersion, setSystemVersion] = useState<string>('1.0.0');

  useEffect(() => {
    // Call the newly implemented system info endpoint to show dynamic status
    api.get('/system/info')
      .then((res) => {
        if (res.data && res.data.success) {
          setSystemStatus('online');
          setSystemVersion(res.data.data.version || '1.0.0');
        } else {
          setSystemStatus('offline');
        }
      })
      .catch(() => {
        setSystemStatus('offline');
      });
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Resolve current section title based on active path
  const currentItem = navItems.find((item) => location.pathname === item.path);
  const pageTitle = currentItem ? currentItem.name : 'AIP Portal';
  const { toasts, removeToast } = useToastStore();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 dark:bg-slate-950 font-sans">
      {/* 1. SIDEBAR NAVIGATION */}
      <aside
        className={cn(
          "relative flex h-full flex-col border-r border-slate-200 bg-white text-slate-900 transition-all duration-300 ease-in-out dark:border-slate-800 dark:bg-slate-900 z-30 shadow-sm",
          isCollapsed ? "w-20" : "w-64"
        )}
      >
        {/* Sidebar Header Brand Area */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-md shadow-primary/20">
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                />
              </svg>
            </div>
            {!isCollapsed && (
              <span className="font-bold text-base tracking-tight text-slate-950 dark:text-white whitespace-nowrap animate-in fade-in duration-300">
                AIP Manager
              </span>
            )}
          </div>
          {!isCollapsed && (
            <button
              onClick={() => setIsCollapsed(true)}
              className="hidden lg:flex h-8 w-8 items-center justify-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Sidebar Navigation Items */}
        <nav className="flex-1 space-y-1.5 p-3 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3.5 px-3.5 py-3 rounded-xl text-sm font-medium transition-all duration-200 group relative",
                    isActive
                      ? "bg-primary text-primary-foreground shadow-lg shadow-primary/10"
                      : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200"
                  )
                }
              >
                <Icon className="h-5 w-5 shrink-0" />
                {!isCollapsed && (
                  <span className="whitespace-nowrap animate-in fade-in duration-300">
                    {item.name}
                  </span>
                )}
                {/* Tooltip on hover when collapsed */}
                {isCollapsed && (
                  <div className="absolute left-16 z-50 rounded bg-slate-950 px-2 py-1 text-xs font-semibold text-white opacity-0 transition-opacity group-hover:opacity-100 pointer-events-none whitespace-nowrap shadow-md">
                    {item.name}
                  </div>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Sidebar Footer System details */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/40">
          {isCollapsed ? (
            <div className="flex justify-center">
              <Server className={cn(
                "h-5 w-5",
                systemStatus === 'online' ? "text-green-500" : systemStatus === 'offline' ? "text-destructive" : "text-slate-400 animate-pulse"
              )} />
            </div>
          ) : (
            <div className="space-y-2 animate-in fade-in duration-300">
              <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
                <Activity className="h-3.5 w-3.5" />
                <span>Backend v{systemVersion}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={cn(
                  "h-2 w-2 rounded-full",
                  systemStatus === 'online' ? "bg-green-500 animate-pulse" : systemStatus === 'offline' ? "bg-destructive" : "bg-slate-400 animate-pulse"
                )} />
                <span className="text-[11px] font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                  {systemStatus === 'online' ? "Online" : systemStatus === 'offline' ? "Offline" : "Connecting..."}
                </span>
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* 2. MAIN APP CONTENT CONTAINER */}
      <div className="flex flex-col flex-1 h-full overflow-hidden">
        {/* Top Navbar */}
        <header className="flex h-16 w-full items-center justify-between border-b border-slate-200 bg-white px-6 dark:border-slate-800 dark:bg-slate-900 z-20 shadow-sm shrink-0">
          <div className="flex items-center gap-4">
            {isCollapsed && (
              <button
                onClick={() => setIsCollapsed(false)}
                className="h-9 w-9 flex items-center justify-center rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 transition-colors"
              >
                <Menu className="h-5 w-5" />
              </button>
            )}
            <h1 className="text-lg font-bold text-slate-950 dark:text-white">
              {pageTitle}
            </h1>
          </div>

          <div className="flex items-center gap-4">
            <NotificationCenter />

            {/* User Profile dropdown */}
            <div className="relative">
            <button
              onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
              onBlur={() => setTimeout(() => setProfileDropdownOpen(false), 200)}
              className="flex items-center gap-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 p-1.5 pr-3 hover:bg-slate-100 dark:bg-slate-950/40 dark:hover:bg-slate-850 transition-all duration-200 outline-none"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary font-bold text-sm">
                {user?.full_name ? user.full_name.charAt(0) : 'U'}
              </div>
              <div className="hidden sm:block text-left">
                <p className="text-xs font-bold text-slate-900 dark:text-white leading-none">
                  {user?.full_name}
                </p>
                <p className="text-[10px] text-slate-500 font-semibold leading-none mt-1">
                  {user?.role}
                </p>
              </div>
            </button>

            {/* Profile Menu Dropdown */}
            {profileDropdownOpen && (
              <Card className="absolute right-0 mt-2 w-56 border-slate-200/80 bg-white p-2 shadow-2xl dark:border-slate-800 dark:bg-slate-900 animate-in fade-in slide-in-from-top-2 duration-150 z-50">
                <div className="px-3 py-2 border-b border-slate-100 dark:border-slate-800/50 mb-1">
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Signed in as</p>
                  <p className="text-sm font-bold text-slate-900 dark:text-white truncate mt-0.5">{user?.email}</p>
                </div>
                <div className="px-3 py-1 flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400">
                  <Shield className="h-3.5 w-3.5 text-primary" />
                  <span>Access: <b>{user?.role}</b></span>
                </div>
                <hr className="border-slate-100 dark:border-slate-800/50 my-1" />
                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-destructive hover:bg-destructive/10 dark:hover:bg-destructive/20 transition-all duration-200"
                >
                  <LogOut className="h-4 w-4" />
                  Sign Out
                </button>
              </Card>
            )}
          </div>
        </div>
      </header>

        {/* Viewport content containing nested subpages */}
        <main className="flex-1 overflow-y-auto p-8 bg-slate-50 dark:bg-slate-950/20">
          <div className="mx-auto max-w-7xl">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Floating Global Toasts Overlay */}
      <div className="fixed bottom-5 right-5 z-[9999] flex flex-col gap-2.5 max-w-sm w-full">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            onClick={() => removeToast(toast.id)}
            className={cn(
              "flex items-start gap-3 p-4 rounded-2xl border shadow-xl cursor-pointer transition-all duration-300 animate-in slide-in-from-bottom-5 fade-in hover:scale-[1.02]",
              toast.type === 'success'
                ? "bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-950/90 dark:border-emerald-800 dark:text-emerald-200"
                : toast.type === 'error'
                ? "bg-rose-50 border-rose-200 text-rose-800 dark:bg-rose-950/90 dark:border-rose-800 dark:text-rose-200"
                : "bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-950/90 dark:border-blue-800 dark:text-blue-200"
            )}
          >
            <div className="flex-1 text-sm font-bold leading-tight">
              {toast.message}
            </div>
            <button className="text-xs font-black opacity-60 hover:opacity-100 transition-opacity">×</button>
          </div>
        ))}
      </div>
    </div>
  );
}
