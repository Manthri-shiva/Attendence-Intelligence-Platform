import React, { useState, useEffect } from 'react';
import api from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { useToastStore } from '@/store/toastStore';
import { useAuthStore } from '@/store/authStore';
import { FileText, Download, Calendar, Loader2, Filter, Settings } from 'lucide-react';

interface SimpleRef {
  id: number;
  name: string;
}

interface MemberRef {
  id: number;
  full_name: string;
}

export default function ReportsPage() {
  const { user } = useAuthStore();
  const { addToast } = useToastStore();

  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState<string | null>(null);

  // Aux Lists
  const [depts, setDepts] = useState<SimpleRef[]>([]);
  const [teams, setTeams] = useState<SimpleRef[]>([]);
  const [members, setMembers] = useState<MemberRef[]>([]);

  // Filter Form State
  const [format, setFormat] = useState('csv');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [deptId, setDeptId] = useState('');
  const [teamId, setTeamId] = useState('');
  const [memberId, setMemberId] = useState('');
  const [attendanceStatus, setAttendanceStatus] = useState('');

  const loadHelpers = async () => {
    try {
      const deptsRes = await api.get('/departments/?limit=100');
      if (deptsRes.data?.success) setDepts(deptsRes.data.data || []);

      const teamsRes = await api.get('/teams/?limit=100');
      if (teamsRes.data?.success) setTeams(teamsRes.data.data || []);

      const usersRes = await api.get('/users/?limit=200');
      if (usersRes.data?.success) setMembers(usersRes.data.data || []);
    } catch {
      // Fail silently
    }
  };

  useEffect(() => {
    loadHelpers();
  }, []);

  const handleExport = async (e: React.FormEvent) => {
    e.preventDefault();
    setExporting(format);
    try {
      let queryStr = `/reports/export?format=${format}`;
      if (startDate) queryStr += `&start_date=${startDate}`;
      if (endDate) queryStr += `&end_date=${endDate}`;
      if (deptId) queryStr += `&department_id=${deptId}`;
      if (teamId) queryStr += `&team_id=${teamId}`;
      if (memberId) queryStr += `&member_id=${memberId}`;
      if (attendanceStatus) queryStr += `&status=${attendanceStatus}`;

      // Call API expecting blob response
      const res = await api.get(queryStr, { responseType: 'blob' });
      
      // Determine filename matching ext
      const ext = format === 'pdf' ? 'html' : format === 'excel' ? 'xls' : 'csv';
      const filename = `attendance_report_${new Date().toISOString().split('T')[0]}.${ext}`;

      const blob = new Blob([res.data], { type: res.headers['content-type']?.toString() || 'application/octet-stream' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);

      addToast(`Report downloaded successfully in ${format.toUpperCase()} format.`, 'success');
    } catch (err) {
      addToast('Failed to generate report export. Please check filter constraints.', 'error');
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          Reports
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Export daily timesheets, audit logs, and compliance spreadsheets across departments.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* FILTERS COLUMN */}
        <Card className="border-slate-200 dark:border-slate-800 md:col-span-1">
          <CardHeader>
            <CardTitle className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Filter className="h-4.5 w-4.5 text-primary" />
              Report Configuration
            </CardTitle>
            <CardDescription className="text-xs text-slate-400">Configure parameters and filters.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleExport} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="repFormat">Export Format</Label>
                <select
                  id="repFormat"
                  value={format}
                  onChange={(e) => setFormat(e.target.value)}
                  className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                >
                  <option value="csv">CSV Sheet (.csv)</option>
                  <option value="excel">Excel Document (.xls)</option>
                  <option value="pdf">Styled HTML Report (.html / .pdf)</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="repStart">Start Date</Label>
                  <input
                    id="repStart"
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="repEnd">End Date</Label>
                  <input
                    id="repEnd"
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="repDept">Department</Label>
                <select
                  id="repDept"
                  value={deptId}
                  onChange={(e) => setDeptId(e.target.value)}
                  className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                >
                  <option value="">All Departments</option>
                  {depts.map((d) => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="repTeam">Team</Label>
                <select
                  id="repTeam"
                  value={teamId}
                  onChange={(e) => setTeamId(e.target.value)}
                  className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                >
                  <option value="">All Teams</option>
                  {teams.map((t) => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="repMember">Participant</Label>
                <select
                  id="repMember"
                  value={memberId}
                  onChange={(e) => setMemberId(e.target.value)}
                  className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                >
                  <option value="">All Members</option>
                  {members.map((m) => (
                    <option key={m.id} value={m.id}>{m.full_name}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="repStatus">Attendance Status</Label>
                <select
                  id="repStatus"
                  value={attendanceStatus}
                  onChange={(e) => setAttendanceStatus(e.target.value)}
                  className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                >
                  <option value="">All Statuses</option>
                  <option value="Present">Present</option>
                  <option value="Late">Late</option>
                  <option value="Absent">Absent</option>
                  <option value="Excused">Excused</option>
                  <option value="Pending Approval">Pending AI Approval</option>
                </select>
              </div>

              <Button type="submit" disabled={exporting !== null} className="w-full rounded-xl gap-2 font-semibold">
                {exporting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generating export...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4" />
                    Generate & Download
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* INFO COLUMN */}
        <Card className="border-slate-200 dark:border-slate-800 md:col-span-2 shadow-sm bg-white dark:bg-slate-900">
          <CardHeader>
            <div className="flex items-center gap-2 text-primary">
              <FileText className="h-5 w-5" />
              <CardTitle className="text-base font-bold text-slate-900 dark:text-white">Generated Reports & Auditing</CardTitle>
            </div>
            <CardDescription className="text-xs text-slate-400">
              Download standard compliance sheets. Exports are recorded in the system audit logs.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 p-4 space-y-3">
              <h4 className="text-xs font-black uppercase text-slate-400">Export Policies</h4>
              <ul className="text-xs text-slate-650 dark:text-slate-400 space-y-2 list-disc list-inside">
                <li>Daily outputs capture real-time geofence matches.</li>
                <li>Mismatches and liveness alerts are highlighted under AI Pending filters.</li>
                <li>All exports log actor identifiers and timestamp parameters.</li>
              </ul>
            </div>

            <div className="text-center py-12 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-2xl">
              <Calendar className="h-10 w-10 text-slate-350 dark:text-slate-650 mx-auto mb-3" />
              <p className="text-slate-600 dark:text-slate-400 font-semibold">Export Engine Ready</p>
              <p className="text-xs text-slate-400 mt-1">Select filters on the left panel to output compliance sheets.</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
