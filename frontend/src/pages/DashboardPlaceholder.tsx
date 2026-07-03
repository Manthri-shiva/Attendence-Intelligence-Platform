import React from 'react';
import { useAuthStore } from '@/store/authStore';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LogOut, User as UserIcon, Shield, CheckCircle } from 'lucide-react';

export default function DashboardPlaceholder() {
  const { user, logout } = useAuthStore();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 text-center dark:bg-slate-950">
      <div className="max-w-md w-full animate-in fade-in zoom-in-95 duration-300">
        <Card className="border-slate-200 bg-white shadow-xl dark:border-slate-800 dark:bg-slate-900">
          <CardHeader className="flex flex-col items-center pb-2">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-100 text-blue-600 dark:bg-blue-900/50 dark:text-blue-300 shadow-md">
              <UserIcon className="h-8 w-8" />
            </div>
            <CardTitle className="mt-4 text-2xl font-bold tracking-tight">
              Welcome Back
            </CardTitle>
            <CardDescription className="text-slate-500">
              Attendance Intelligence Platform Admin Workspace
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 pt-4 text-left">
            <div className="rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-800 p-4 space-y-3">
              <div className="flex justify-between items-center border-b border-slate-200/50 dark:border-slate-800/50 pb-2">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">User</span>
                <span className="text-sm font-semibold text-slate-900 dark:text-white">{user?.full_name}</span>
              </div>
              <div className="flex justify-between items-center border-b border-slate-200/50 dark:border-slate-800/50 pb-2">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Email</span>
                <span className="text-sm text-slate-700 dark:text-slate-300">{user?.email}</span>
              </div>
              <div className="flex justify-between items-center border-b border-slate-200/50 dark:border-slate-800/50 pb-2">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Role</span>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 border border-blue-100 dark:border-blue-900/30">
                  <Shield className="h-3 w-3" />
                  {user?.role}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</span>
                <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-0.5 text-xs font-semibold text-green-700 dark:bg-green-950/40 dark:text-green-300">
                  <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
                  Active
                </span>
              </div>
            </div>
            
            <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 bg-blue-50/35 dark:bg-blue-950/5 p-3 rounded-lg border border-blue-500/10">
              <CheckCircle className="h-4 w-4 shrink-0 text-blue-500" />
              <span>Session Authenticated: JWT token loaded and attached to authorization headers.</span>
            </div>

            <Button onClick={logout} className="w-full h-11" variant="destructive">
              <LogOut className="mr-2 h-4 w-4" />
              Sign Out
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
