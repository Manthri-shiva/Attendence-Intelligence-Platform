import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Building2, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function OrganizationsPage() {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Organizations
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Manage global enterprise organization profiles and scopes.
          </p>
        </div>
        <Button disabled className="gap-2">
          <Plus className="h-4 w-4" />
          Add Organization
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2 text-primary">
            <Building2 className="h-5 w-5" />
            <CardTitle>Enterprise Registry</CardTitle>
          </div>
          <CardDescription>
            Database integration is pending. Enterprise data will display once PostgreSQL is active.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-2xl">
            <p className="text-slate-500 dark:text-slate-400 font-medium">No organizations configured.</p>
            <p className="text-xs text-slate-400 mt-1">Enterprise organizational nodes are currently mocked in the app shell.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
