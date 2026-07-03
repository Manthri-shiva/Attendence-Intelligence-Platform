import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Briefcase, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function DepartmentsPage() {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Departments
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Configure functional departments, sites, and coordinator mappings.
          </p>
        </div>
        <Button disabled className="gap-2">
          <Plus className="h-4 w-4" />
          Add Department
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2 text-primary">
            <Briefcase className="h-5 w-5" />
            <CardTitle>Functional Departments</CardTitle>
          </div>
          <CardDescription>
            Configure departments and active shifts. Mapped configurations will render here.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-2xl">
            <p className="text-slate-500 dark:text-slate-400 font-medium">No active departments found.</p>
            <p className="text-xs text-slate-400 mt-1">Departments and shifts can be registered once API storage is integrated.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
