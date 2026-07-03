import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { CalendarCheck, Shield } from 'lucide-react';

export default function AttendancePage() {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          Attendance
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Monitor real-time clock-in logs, geofencing coordinates, and verification overrides.
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2 text-primary">
            <CalendarCheck className="h-5 w-5" />
            <CardTitle>Attendance Log</CardTitle>
          </div>
          <CardDescription>
            Live verification streams are disabled. GPS / Facial authentication modules will be built in subsequent milestones.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3 rounded-xl border border-blue-500/10 bg-blue-500/5 p-4 text-sm text-blue-600 dark:text-blue-400">
            <Shield className="h-5 w-5 shrink-0" />
            <span>Attendance logic, camera integrations, GPS verification, and real-time trackers are out of scope for Milestone 3.</span>
          </div>
          <div className="text-center py-12 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-2xl mt-6">
            <p className="text-slate-500 dark:text-slate-400 font-medium">No check-in logs recorded.</p>
            <p className="text-xs text-slate-400 mt-1">Live tracking logs will be integrated when clock-in components are developed.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
