import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Users, Calendar, Building, Clock, ShieldAlert, CheckCircle, AlertTriangle,
  Play, CheckSquare, Sparkles, BarChart2, ShieldCheck, Activity, AlertCircle, CheckCircle2
} from 'lucide-react';
import api from '@/services/api';

interface DashboardStats {
  total_organizations: number;
  total_departments: number;
  total_teams: number;
  total_members: number;
  total_sessions: number;
  active_sessions: number;
  completed_sessions: number;
  attendance_percentage: number;
  present_count: number;
  late_count: number;
  absent_count: number;
  excused_count: number;
  pending_ai_approvals: number;
  average_session_duration: number;
  ai_verification_success_rate: number;
  ai_verification_failure_rate: number;
  today_attendance?: number;
  verified_attendance?: number;
  pending_verification?: number;
  rejected_attendance?: number;
}

interface ChartTrendPoint {
  date: string;
  present: number;
  absent: number;
}

interface ChartDeptPoint {
  name: string;
  rate: number;
}

interface ChartPiePoint {
  name: string;
  value: number;
}

interface ChartsData {
  daily_attendance_trend: ChartTrendPoint[];
  weekly_attendance_trend: { week: string; present: number; absent: number }[];
  attendance_by_department: ChartDeptPoint[];
  attendance_by_team: ChartDeptPoint[];
  attendance_by_organization: ChartDeptPoint[];
  ai_verification_success_vs_failure: ChartPiePoint[];
  session_completion_trend: { date: string; scheduled: number; completed: number }[];
}

export default function DashboardPage() {
  const { user } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [charts, setCharts] = useState<ChartsData | null>(null);

  const fetchDashboard = async () => {
    try {
      const statsRes = await api.get('/analytics/dashboard');
      if (statsRes.data?.success) setStats(statsRes.data.data);

      const chartsRes = await api.get('/analytics/charts');
      if (chartsRes.data?.success) setCharts(chartsRes.data.data);
    } catch {
      // Fail silently
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const metaCards = [
    { name: 'Attendance Rate', value: stats ? `${stats.attendance_percentage}%` : '0%', change: 'Present & Late ratio', icon: Activity, color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
    { name: 'Active Sessions', value: stats ? String(stats.active_sessions) : '0', change: 'Running check-ins', icon: Play, color: 'text-blue-500', bg: 'bg-blue-500/10' },
    { name: 'Pending AI approvals', value: stats ? String(stats.pending_ai_approvals) : '0', change: 'Biometric overrides', icon: ShieldAlert, color: 'text-amber-500', bg: 'bg-amber-500/10' },
    { name: 'Registered Members', value: stats ? String(stats.total_members) : '0', change: 'Active platform users', icon: Users, color: 'text-indigo-500', bg: 'bg-indigo-500/10' }
  ];

  const evidenceCards = [
    { name: "Today's Attendance", value: stats ? String(stats.today_attendance || 0) : '0', change: 'Checked in today', icon: Calendar, color: 'text-indigo-500', bg: 'bg-indigo-500/10' },
    { name: 'Verified Attendance', value: stats ? String(stats.verified_attendance || 0) : '0', change: 'AI Face & GPS confirmed', icon: CheckCircle2, color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
    { name: 'Pending Verification', value: stats ? String(stats.pending_verification || 0) : '0', change: 'Manual approval review list', icon: Clock, color: 'text-amber-500', bg: 'bg-amber-500/10' },
    { name: 'Rejected Attendance', value: stats ? String(stats.rejected_attendance || 0) : '0', change: 'Spoof / Low confidence count', icon: AlertCircle, color: 'text-rose-500', bg: 'bg-rose-500/10' }
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Welcome Card */}
      <div className="rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-white shadow-lg flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold tracking-tight">
            Welcome, {user?.full_name || 'Administrator'}!
          </h2>
          <p className="mt-1.5 text-blue-100 max-w-xl text-xs font-medium">
            PostgreSQL metrics and AI anti-spoof logs are compiled. Review live rosters, check-in geofence logs, and approval notifications.
          </p>
        </div>
        <Sparkles className="h-10 w-10 text-blue-200 opacity-60 hidden sm:block animate-pulse" />
      </div>

      {loading ? (
        <div className="grid gap-6 md:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="animate-pulse h-28 border-slate-200 dark:border-slate-800" />
          ))}
        </div>
      ) : (
        <>
          {/* Core Dashboard Cards */}
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {metaCards.map((c) => {
              const Icon = c.icon;
              return (
                <Card key={c.name} className="hover:scale-[1.01] transition-all border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      {c.name}
                    </CardTitle>
                    <div className={`p-1.5 rounded-lg ${c.bg} ${c.color}`}>
                      <Icon className="h-4.5 w-4.5" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-black text-slate-900 dark:text-white">
                      {c.value}
                    </div>
                    <p className="text-[10px] text-slate-500 mt-1 font-semibold">{c.change}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Biometric Verification Quick Stats */}
          <div className="space-y-3">
            <h3 className="text-xs font-black text-slate-400 uppercase tracking-wider">Biometric Evidence Metrics</h3>
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {evidenceCards.map((c) => {
                const Icon = c.icon;
                return (
                  <Card key={c.name} className="hover:scale-[1.01] transition-all border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        {c.name}
                      </CardTitle>
                      <div className={`p-1.5 rounded-lg ${c.bg} ${c.color}`}>
                        <Icon className="h-4.5 w-4.5" />
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-black text-slate-900 dark:text-white">
                        {c.value}
                      </div>
                      <p className="text-[10px] text-slate-500 mt-1 font-semibold">{c.change}</p>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>

          {/* DETAILED STATS GRID */}
          <div className="grid gap-6 md:grid-cols-3">
            {/* 1. Status Splits */}
            <Card className="border-slate-200 dark:border-slate-800">
              <CardHeader className="pb-3">
                <CardTitle className="text-xs font-black uppercase text-slate-400">Attendance splits</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3.5">
                <div className="flex justify-between items-center text-xs font-semibold text-slate-600 dark:text-slate-400">
                  <span className="flex items-center gap-1.5"><CheckCircle className="h-4 w-4 text-emerald-500" /> Present</span>
                  <span className="font-bold text-slate-950 dark:text-white">{stats?.present_count || 0}</span>
                </div>
                <div className="flex justify-between items-center text-xs font-semibold text-slate-600 dark:text-slate-400">
                  <span className="flex items-center gap-1.5"><Clock className="h-4 w-4 text-amber-500" /> Late</span>
                  <span className="font-bold text-slate-950 dark:text-white">{stats?.late_count || 0}</span>
                </div>
                <div className="flex justify-between items-center text-xs font-semibold text-slate-600 dark:text-slate-400">
                  <span className="flex items-center gap-1.5"><AlertTriangle className="h-4 w-4 text-red-500" /> Absent</span>
                  <span className="font-bold text-slate-950 dark:text-white">{stats?.absent_count || 0}</span>
                </div>
                <div className="flex justify-between items-center text-xs font-semibold text-slate-600 dark:text-slate-400">
                  <span className="flex items-center gap-1.5"><CheckSquare className="h-4 w-4 text-indigo-500" /> Excused</span>
                  <span className="font-bold text-slate-950 dark:text-white">{stats?.excused_count || 0}</span>
                </div>
              </CardContent>
            </Card>

            {/* 2. AI verification metrics */}
            <Card className="border-slate-200 dark:border-slate-800">
              <CardHeader className="pb-3">
                <CardTitle className="text-xs font-black uppercase text-slate-400">AI Verification Performance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500">AI Match Success:</span>
                  <span className="text-sm font-black text-emerald-600">{stats?.ai_verification_success_rate || 0}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500">AI Match Failure:</span>
                  <span className="text-sm font-black text-red-650">{stats?.ai_verification_failure_rate || 0}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500">Avg check-in duration:</span>
                  <span className="text-sm font-black text-indigo-650">{stats?.average_session_duration || 0} mins</span>
                </div>
              </CardContent>
            </Card>

            {/* 3. System Configuration counts */}
            <Card className="border-slate-200 dark:border-slate-800">
              <CardHeader className="pb-3">
                <CardTitle className="text-xs font-black uppercase text-slate-400">Directory Directory Configurations</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3.5 text-xs text-slate-650 dark:text-slate-400">
                <div className="flex justify-between">
                  <span>Organizations:</span>
                  <span className="font-bold text-slate-900 dark:text-white">{stats?.total_organizations || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Departments:</span>
                  <span className="font-bold text-slate-900 dark:text-white">{stats?.total_departments || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Teams:</span>
                  <span className="font-bold text-slate-900 dark:text-white">{stats?.total_teams || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Total Scheduled Sessions:</span>
                  <span className="font-bold text-slate-900 dark:text-white">{stats?.total_sessions || 0}</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* INTERACTIVE CUSTOM SVG CHARTS */}
          {charts && (
            <div className="grid gap-6 md:grid-cols-2">
              {/* Daily Attendance Trend (Line Chart) */}
              <Card className="border-slate-200 dark:border-slate-800">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-bold flex items-center gap-1.5"><Activity className="h-4.5 w-4.5 text-primary" /> Daily Attendance Trend</CardTitle>
                  <CardDescription className="text-[10px] text-slate-400">Scan volume of Present & Absent members (past 7 days).</CardDescription>
                </CardHeader>
                <CardContent className="p-4 flex items-center justify-center">
                  <svg viewBox="0 0 450 180" className="w-full h-auto">
                    {/* Grid Lines */}
                    {[30, 70, 110, 150].map((y, idx) => (
                      <line key={idx} x1="40" y1={y} x2="430" y2={y} stroke="#f1f5f9" strokeWidth="1" strokeDasharray="3" />
                    ))}
                    {/* Graph paths */}
                    {(() => {
                      const maxVal = Math.max(...charts.daily_attendance_trend.map(d => Math.max(d.present, d.absent, 5)));
                      const points = charts.daily_attendance_trend.map((pt, idx) => {
                        const x = 50 + idx * 60;
                        const yPres = 150 - (pt.present / maxVal) * 110;
                        const yAbs = 150 - (pt.absent / maxVal) * 110;
                        return { x, yPres, yAbs, date: pt.date };
                      });

                      const pathPres = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.yPres}`).join(' ');
                      const pathAbs = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.yAbs}`).join(' ');

                      return (
                        <>
                          {/* Present Line */}
                          <path d={pathPres} fill="none" stroke="#2563eb" strokeWidth="2.5" strokeLinecap="round" />
                          {/* Absent Line */}
                          <path d={pathAbs} fill="none" stroke="#dc2626" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="4" />
                          
                          {/* Circle Markers */}
                          {points.map((p, idx) => (
                            <g key={idx}>
                              <circle cx={p.x} cy={p.yPres} r="4" fill="#2563eb" />
                              <circle cx={p.x} cy={p.yAbs} r="4" fill="#dc2626" />
                              <text x={p.x} y="170" fontSize="9" textAnchor="middle" fill="#94a3b8" fontWeight="bold">{p.date}</text>
                            </g>
                          ))}
                        </>
                      );
                    })()}
                    <line x1="40" y1="150" x2="430" y2="150" stroke="#cbd5e1" strokeWidth="1" />
                  </svg>
                </CardContent>
              </Card>

              {/* Attendance by Department (Bar Chart) */}
              <Card className="border-slate-200 dark:border-slate-800">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-bold flex items-center gap-1.5"><BarChart2 className="h-4.5 w-4.5 text-indigo-500" /> Attendance by Department</CardTitle>
                  <CardDescription className="text-[10px] text-slate-400">Attendance percentages scoped by configured departments.</CardDescription>
                </CardHeader>
                <CardContent className="p-4 flex items-center justify-center">
                  <svg viewBox="0 0 450 180" className="w-full h-auto">
                    <line x1="40" y1="150" x2="430" y2="150" stroke="#cbd5e1" strokeWidth="1" />
                    {charts.attendance_by_department.length === 0 ? (
                      <text x="225" y="90" fill="#94a3b8" fontSize="12" textAnchor="middle">No department data recorded.</text>
                    ) : (
                      charts.attendance_by_department.map((dept, idx) => {
                        const x = 50 + idx * 75;
                        const barHeight = (dept.rate / 100) * 110;
                        const y = 150 - barHeight;
                        return (
                          <g key={idx}>
                            <rect x={x} y={y} width="28" height={barHeight} fill="#4f46e5" rx="3" />
                            <text x={x + 14} y={y - 6} fontSize="9" textAnchor="middle" fontWeight="bold" fill="#4f46e5">{dept.rate}%</text>
                            <text x={x + 14} y="165" fontSize="8" textAnchor="middle" fill="#94a3b8" fontWeight="bold">{dept.name.slice(0, 10)}</text>
                          </g>
                        );
                      })
                    )}
                  </svg>
                </CardContent>
              </Card>

              {/* AI Verification Success vs Failure (Donut Pie Chart) */}
              <Card className="border-slate-200 dark:border-slate-800">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-bold flex items-center gap-1.5"><ShieldCheck className="h-4.5 w-4.5 text-emerald-500" /> AI Verification Success Rate</CardTitle>
                  <CardDescription className="text-[10px] text-slate-400">Biometric facial match & spoof-prevention checks splits.</CardDescription>
                </CardHeader>
                <CardContent className="p-4 flex items-center justify-center">
                  {(() => {
                    const success = charts.ai_verification_success_vs_failure.find(x => x.name === 'Verified')?.value || 0;
                    const fail = charts.ai_verification_success_vs_failure.find(x => x.name === 'Mismatches/Pending')?.value || 0;
                    const total = success + fail;
                    
                    const successRate = total > 0 ? (success / total) * 100.0 : 100.0;
                    const failRate = total > 0 ? (fail / total) * 100.0 : 0.0;

                    // Dasharray calculations for radius=50 (perimeter=314.16)
                    const successDash = (successRate / 100) * 314.16;
                    const failDash = 314.16 - successDash;

                    return (
                      <div className="flex flex-col sm:flex-row items-center gap-12 w-full justify-center">
                        <svg width="150" height="150" viewBox="0 0 150 150">
                          {/* Background Circle */}
                          <circle cx="75" cy="75" r="50" fill="none" stroke="#f1f5f9" strokeWidth="18" />
                          
                          {/* Success Segment */}
                          <circle
                            cx="75"
                            cy="75"
                            r="50"
                            fill="none"
                            stroke="#10b981"
                            strokeWidth="18"
                            strokeDasharray={`${successDash} 314.16`}
                            transform="rotate(-90 75 75)"
                            strokeLinecap="round"
                          />
                          
                          {/* Text Indicator in Center */}
                          <text x="75" y="80" fontSize="14" fontWeight="bold" textAnchor="middle" fill="#1e293b">
                            {successRate.toFixed(0)}%
                          </text>
                        </svg>
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-xs font-semibold">
                            <span className="w-3 h-3 rounded-full bg-emerald-500" />
                            <span>AI Verified: {success} ({successRate.toFixed(0)}%)</span>
                          </div>
                          <div className="flex items-center gap-2 text-xs font-semibold">
                            <span className="w-3 h-3 rounded-full bg-slate-300" />
                            <span>Mismatches/Pending: {fail} ({failRate.toFixed(0)}%)</span>
                          </div>
                        </div>
                      </div>
                    );
                  })()}
                </CardContent>
              </Card>

              {/* Session Completion Trend (Scheduled vs Completed) */}
              <Card className="border-slate-200 dark:border-slate-800">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-bold flex items-center gap-1.5"><Calendar className="h-4.5 w-4.5 text-blue-500" /> Session Activity (Completion Trend)</CardTitle>
                  <CardDescription className="text-[10px] text-slate-400">Total sessions scheduled vs completed daily.</CardDescription>
                </CardHeader>
                <CardContent className="p-4 flex items-center justify-center">
                  <svg viewBox="0 0 450 180" className="w-full h-auto">
                    <line x1="40" y1="150" x2="430" y2="150" stroke="#cbd5e1" strokeWidth="1" />
                    {charts.session_completion_trend.map((s, idx) => {
                      const x = 50 + idx * 60;
                      // Max count simulation
                      const maxVal = Math.max(...charts.session_completion_trend.map(item => item.scheduled + item.completed), 3);
                      
                      const heightSched = (s.scheduled / maxVal) * 110;
                      const heightCompl = (s.completed / maxVal) * 110;

                      return (
                        <g key={idx}>
                          {/* Scheduled Bar */}
                          <rect x={x} y={150 - heightSched} width="12" height={heightSched} fill="#93c5fd" rx="1" />
                          {/* Completed Bar */}
                          <rect x={x + 14} y={150 - heightCompl} width="12" height={heightCompl} fill="#2563eb" rx="1" />
                          
                          <text x={x + 13} y="165" fontSize="8" textAnchor="middle" fill="#94a3b8" fontWeight="bold">{s.date}</text>
                        </g>
                      );
                    })}
                  </svg>
                </CardContent>
              </Card>
            </div>
          )}
        </>
      )}
    </div>
  );
}
