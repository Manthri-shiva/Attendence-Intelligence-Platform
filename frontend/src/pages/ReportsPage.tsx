import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { FileText, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function ReportsPage() {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Reports
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Export daily timesheets, audit logs, and anomaly detection spreadsheets.
          </p>
        </div>
        <Button disabled className="gap-2">
          <Download className="h-4 w-4" />
          Export Timesheets
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2 text-primary">
            <FileText className="h-5 w-5" />
            <CardTitle>Generated Timesheets & Audits</CardTitle>
          </div>
          <CardDescription>
            Audit logs and reporting engines are disabled during this phase of UI integration.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-2xl">
            <p className="text-slate-500 dark:text-slate-400 font-medium">No audit spreadsheets available.</p>
            <p className="text-xs text-slate-400 mt-1">Analytics engine and exports will activate during Milestone 6 development.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
