import React from 'react';
import { useAuthStore } from '@/store/authStore';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, Calendar, Building, Clock, ShieldAlert } from 'lucide-react';

export default function DashboardPage() {
  const { user } = useAuthStore();

  const stats = [
    { name: 'Total Registered Members', value: '1,248', change: '+12% from last month', icon: Users, color: 'text-blue-500' },
    { name: 'Overall Daily Attendance', value: '94.8%', change: '+0.5% from yesterday', icon: Calendar, color: 'text-green-500' },
    { name: 'Departments Configured', value: '18', change: 'Across 3 primary sites', icon: Building, color: 'text-indigo-500' },
    { name: 'Average Check-in Time', value: '08:42 AM', change: 'Within policy window', icon: Clock, color: 'text-amber-500' },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Welcome Card */}
      <div className="rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 p-8 text-white shadow-lg">
        <h2 className="text-3xl font-extrabold tracking-tight">
          Welcome, {user?.full_name || 'Administrator'}!
        </h2>
        <p className="mt-2 text-blue-100 max-w-xl text-sm font-medium">
          AIP dashboard is currently initialized in **Application Shell Sandbox** mode. Verify sidebar links, system indicators, and route permissions.
        </p>
      </div>

      {/* Grid of Metric Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.name} className="hover:scale-[1.02] transition-transform duration-300">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  {stat.name}
                </CardTitle>
                <div className={`p-2 rounded-xl bg-slate-50 dark:bg-slate-900 ${stat.color}`}>
                  <Icon className="h-5 w-5" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
                  {stat.value}
                </div>
                <p className="text-xs text-slate-500 mt-2 font-medium">
                  {stat.change}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Role Capabilities Quick Info */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2 text-primary">
            <ShieldAlert className="h-5 w-5" />
            <CardTitle>Role Capabilities & Context</CardTitle>
          </div>
          <CardDescription>
            Verify system behavior mapping for your current authenticated profile.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-xl border border-slate-150 dark:border-slate-800 bg-slate-50/50 p-4">
            <h4 className="text-sm font-bold text-slate-900 dark:text-white">Current Logged-in Session Profile</h4>
            <div className="grid gap-2 sm:grid-cols-2 mt-3 text-sm text-slate-600 dark:text-slate-400">
              <p>Email Address: <b>{user?.email}</b></p>
              <p>Assigned Security Role: <b>{user?.role}</b></p>
              <p>Active Status: <span className="text-green-600 font-semibold">Active Account</span></p>
              <p>Database Scope: <span className="text-amber-600 font-semibold">Mocked In-Memory</span></p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
