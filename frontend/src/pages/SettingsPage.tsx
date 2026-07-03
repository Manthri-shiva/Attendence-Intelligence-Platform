import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Settings, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function SettingsPage() {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Settings
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Configure system variables, validation tolerance levels, and alert rules.
          </p>
        </div>
        <Button disabled className="gap-2">
          <Save className="h-4 w-4" />
          Save Changes
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2 text-primary">
            <Settings className="h-5 w-5" />
            <CardTitle>System Configurations</CardTitle>
          </div>
          <CardDescription>
            Configure validation thresholds and threshold bounds for verification checks.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-2xl">
            <p className="text-slate-500 dark:text-slate-400 font-medium">Settings storage inactive.</p>
            <p className="text-xs text-slate-400 mt-1">System preferences and parameters will persist once metadata repositories are active.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
