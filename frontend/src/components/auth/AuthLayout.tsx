import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';

export default function AuthLayout() {
  const { isAuthenticated } = useAuthStore();

  // If already authenticated, redirect immediately to dashboard
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="relative flex min-h-screen flex-col justify-center overflow-hidden bg-slate-50 py-12 px-4 sm:px-6 lg:px-8 dark:bg-slate-950">
      {/* Decorative background gradients */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-100/40 via-sky-50/10 to-slate-50 dark:from-blue-950/20 dark:via-slate-950 dark:to-slate-950" />
      
      {/* Pulsing blurred gradient orbs for high-end aesthetic value */}
      <div className="absolute -top-40 -right-40 h-[600px] w-[600px] rounded-full bg-blue-400/10 blur-3xl filter dark:bg-blue-600/5 animate-pulse" />
      <div className="absolute -bottom-40 -left-40 h-[600px] w-[600px] rounded-full bg-indigo-400/10 blur-3xl filter dark:bg-indigo-600/5 animate-pulse" />

      <div className="relative z-10 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex flex-col items-center">
          {/* Logo container */}
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-xl shadow-primary/20">
            <svg
              className="h-6 w-6"
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
          <h2 className="mt-6 text-center text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Attendance Intelligence
          </h2>
          <p className="mt-2 text-center text-sm text-slate-500 dark:text-slate-400">
            AIP Secure Gateway
          </p>
        </div>

        <div className="mt-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
