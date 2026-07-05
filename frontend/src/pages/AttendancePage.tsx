import React, { useState, useEffect } from 'react';
import api from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Calendar, Table, Plus, Edit2, Trash2, Search, Loader2, Play, Pause, CheckCircle,
  XCircle, Archive, MapPin, Users, UserPlus, Trash, ShieldCheck, Clock, Award, ShieldAlert
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToastStore } from '@/store/toastStore';
import { useAuthStore } from '@/store/authStore';
import { useNavigate } from 'react-router-dom';

interface SimpleRef {
  id: number;
  name: string;
}

interface MemberRef {
  id: number;
  full_name: string;
  email: string;
  role: string;
}

interface Session {
  id: number;
  name: string;
  description?: string;
  session_type: string;
  date: string;
  start_time: string;
  end_time: string;
  grace_time: number;
  checkout_time?: string;
  venue?: string;
  gps_radius?: number;
  evidence_type?: string;
  latitude?: number;
  longitude?: number;
  capacity?: number;
  recurrence_pattern?: string;
  recurrence_end_date?: string;
  status: string;
  updated_at: string;
  coordinator?: MemberRef;
  department?: SimpleRef;
  organization?: SimpleRef;
  assigned_members: MemberRef[];
}

interface AttendanceRecord {
  id: number;
  member_id: number;
  status: string;
  check_in_time?: string;
  check_out_time?: string;
  duration?: number;
  member?: MemberRef;
}

export default function AttendancePage() {
  const { user } = useAuthStore();
  const { addToast } = useToastStore();
  const navigate = useNavigate();

  const [activeView, setActiveView] = useState<'calendar' | 'table'>('calendar');
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Aux lists
  const [orgs, setOrgs] = useState<SimpleRef[]>([]);
  const [depts, setDepts] = useState<SimpleRef[]>([]);
  const [coordinatorsList, setCoordinatorsList] = useState<MemberRef[]>([]);
  const [allUsers, setAllUsers] = useState<MemberRef[]>([]);

  // Filters & Pagination
  const [search, setSearch] = useState('');
  const [filterOrg, setFilterOrg] = useState<string>('');
  const [filterDept, setFilterDept] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const limit = 8;

  // Modals
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);
  const [sessionAttendances, setSessionAttendances] = useState<AttendanceRecord[]>([]);
  const [submitting, setSubmitting] = useState(false);

  // Assignment Modal
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [selectedUserIds, setSelectedUserIds] = useState<number[]>([]);

  // Manual Attendance form state
  const [manualMemberId, setManualMemberId] = useState<number | ''>('');
  const [manualStatus, setManualStatus] = useState('Present');

  // Form Fields (Create/Edit)
  const [formName, setFormName] = useState('');
  const [formDesc, setFormDesc] = useState('');
  const [formType, setFormType] = useState('Lecture');
  const [formDate, setFormDate] = useState('');
  const [formStart, setFormStart] = useState('09:00:00');
  const [formEnd, setFormEnd] = useState('11:00:00');
  const [formGrace, setFormGrace] = useState(15);
  const [formVenue, setFormVenue] = useState('');
  const [formGpsRadius, setFormGpsRadius] = useState(50);
  const [formEvidence, setFormEvidence] = useState('GPS');
  const [formLat, setFormLat] = useState<number | ''>('');
  const [formLon, setFormLon] = useState<number | ''>('');
  const [formCapacity, setFormCapacity] = useState<number | ''>('');
  const [formRecurrence, setFormRecurrence] = useState('');
  const [formRecurrenceEnd, setFormRecurrenceEnd] = useState('');
  const [formOrgId, setFormOrgId] = useState<number | ''>('');
  const [formDeptId, setFormDeptId] = useState<number | ''>('');
  const [formCoordId, setFormCoordId] = useState<number | ''>('');

  const loadHelpers = async () => {
    try {
      const orgsRes = await api.get('/organizations/?limit=100');
      if (orgsRes.data?.success) setOrgs(orgsRes.data.data || []);

      const deptsRes = await api.get('/departments/?limit=100');
      if (deptsRes.data?.success) setDepts(deptsRes.data.data || []);

      const usersRes = await api.get('/users/?limit=200');
      if (usersRes.data?.success) {
        const users = usersRes.data.data || [];
        setAllUsers(users);
        setCoordinatorsList(users.filter((u: any) => u.role === 'Coordinator' || u.role === 'OrgAdmin' || u.role === 'SystemAdmin'));
      }
    } catch {
      // Fail silently
    }
  };

  const fetchSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const skip = (page - 1) * limit;
      let queryStr = `/sessions/?skip=${skip}&limit=${limit}&q=${search}`;
      if (filterOrg) queryStr += `&organization_id=${filterOrg}`;
      if (filterDept) queryStr += `&department_id=${filterDept}`;
      if (filterStatus) queryStr += `&status=${filterStatus}`;

      const res = await api.get(queryStr);
      if (res.data?.success) {
        setSessions(res.data.data || []);
        const msg = res.data.message || '';
        const match = msg.match(/Total: (\d+)/);
        setTotalCount(match ? parseInt(match[1]) : (res.data.data?.length || 0));
      } else {
        setError('Failed to fetch session directories.');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred loading scheduled sessions.');
    } finally {
      setLoading(false);
    }
  };

  const fetchSessionDetails = async (sessionId: number) => {
    try {
      const res = await api.get(`/sessions/${sessionId}`);
      if (res.data?.success) {
        setSelectedSession(res.data.data);
      }
      const attRes = await api.get(`/sessions/${sessionId}/attendances`);
      if (attRes.data?.success) {
        setSessionAttendances(attRes.data.data || []);
      }
    } catch {
      addToast('Failed to fetch session metadata or participant rosters.', 'error');
    }
  };

  useEffect(() => {
    loadHelpers();
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [search, filterOrg, filterDept, filterStatus, page]);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName || !formDate || !formStart || !formEnd || !formOrgId) {
      addToast('Please populate all mandatory fields.', 'error');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        name: formName,
        description: formDesc || null,
        session_type: formType,
        date: formDate,
        start_time: formStart.includes(':') && formStart.split(':').length === 2 ? `${formStart}:00` : formStart,
        end_time: formEnd.includes(':') && formEnd.split(':').length === 2 ? `${formEnd}:00` : formEnd,
        grace_time: Number(formGrace),
        venue: formVenue || null,
        gps_radius: formGpsRadius ? Number(formGpsRadius) : null,
        evidence_type: formEvidence,
        latitude: formLat ? Number(formLat) : null,
        longitude: formLon ? Number(formLon) : null,
        capacity: formCapacity ? Number(formCapacity) : null,
        recurrence_pattern: formRecurrence || null,
        recurrence_end_date: formRecurrenceEnd || null,
        organization_id: Number(formOrgId),
        department_id: formDeptId ? Number(formDeptId) : null,
        coordinator_id: formCoordId ? Number(formCoordId) : null
      };

      await api.post('/sessions/', payload);
      addToast('Session scheduled successfully.', 'success');
      setIsCreateModalOpen(false);
      fetchSessions();
    } catch (err: any) {
      addToast(err.response?.data?.message || 'Failed to schedule session.', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleTransitionState = async (sessionId: number, targetState: string) => {
    try {
      let endpoint = '';
      if (targetState === 'Scheduled') endpoint = 'publish';
      else if (targetState === 'Active') endpoint = 'start';
      else if (targetState === 'Paused') endpoint = 'pause';
      else if (targetState === 'Completed') endpoint = 'complete';
      else if (targetState === 'Cancelled') endpoint = 'cancel';
      else if (targetState === 'Archived') endpoint = 'archive';

      await api.post(`/sessions/${sessionId}/${endpoint}`);
      addToast(`Session transitioned to ${targetState}.`, 'success');
      fetchSessionDetails(sessionId);
      fetchSessions();
    } catch (err: any) {
      addToast(err.response?.data?.message || 'State transition failed.', 'error');
    }
  };

  const handleBulkAssign = async () => {
    if (!selectedSession || selectedUserIds.length === 0) return;
    try {
      await api.post(`/sessions/${selectedSession.id}/assign-members`, {
        user_ids: selectedUserIds
      });
      addToast('Participants added successfully.', 'success');
      setIsAssignModalOpen(false);
      setSelectedUserIds([]);
      fetchSessionDetails(selectedSession.id);
    } catch (err: any) {
      addToast(err.response?.data?.message || 'Assignment failed.', 'error');
    }
  };

  const handleRemoveMember = async (userId: number) => {
    if (!selectedSession || !confirm('Remove this member from participant scope?')) return;
    try {
      await api.post(`/sessions/${selectedSession.id}/remove-members`, {
        user_ids: [userId]
      });
      addToast('Member removed.', 'success');
      fetchSessionDetails(selectedSession.id);
    } catch (err: any) {
      addToast(err.response?.data?.message || 'Removal failed.', 'error');
    }
  };

  const handleManualAttendance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSession || !manualMemberId) return;
    try {
      await api.post(`/sessions/${selectedSession.id}/manual-attendance?member_id=${manualMemberId}&status=${manualStatus}`);
      addToast('Attendance log manually updated.', 'success');
      setManualMemberId('');
      fetchSessionDetails(selectedSession.id);
    } catch (err: any) {
      addToast(err.response?.data?.message || 'Override failed.', 'error');
    }
  };

  const handleDeleteSession = async (id: number) => {
    if (!confirm('Are you sure you want to delete this session?')) return;
    try {
      await api.delete(`/sessions/${id}`);
      addToast('Session deleted.', 'success');
      fetchSessions();
    } catch (err: any) {
      addToast(err.response?.data?.message || 'Deletion failed.', 'error');
    }
  };

  const openCreateModal = () => {
    setFormName('');
    setFormDesc('');
    setFormType('Lecture');
    setFormDate(new Date().toISOString().split('T')[0]);
    setFormStart('09:00');
    setFormEnd('11:00');
    setFormGrace(15);
    setFormVenue('');
    setFormGpsRadius(50);
    setFormEvidence('GPS');
    setFormLat('');
    setFormLon('');
    setFormCapacity('');
    setFormRecurrence('');
    setFormRecurrenceEnd('');
    setFormOrgId(user?.organization_id || '');
    setFormDeptId(user?.department_id || '');
    setFormCoordId(user?.id || '');
    setIsCreateModalOpen(true);
  };

  const isCoordinatorOrAbove = user?.role === 'SystemAdmin' || user?.role === 'OrgAdmin' || user?.role === 'Coordinator';
  const totalPages = Math.ceil(totalCount / limit);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Sessions
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Schedule lectures, meetings, coordinate active GPS geofencing tracking, and review participant rosters.
          </p>
        </div>
        {isCoordinatorOrAbove && (
          <Button onClick={openCreateModal} className="gap-2 rounded-xl">
            <Plus className="h-4 w-4" />
            Schedule Session
          </Button>
        )}
      </div>

      {/* FILTER CONTROL BAR */}
      <div className="flex flex-wrap gap-4 items-center justify-between">
        {/* Toggle View */}
        <div className="flex border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden bg-white dark:bg-slate-900">
          <button
            onClick={() => setActiveView('calendar')}
            className={`px-4 py-2 text-sm font-semibold flex items-center gap-1.5 transition-colors ${
              activeView === 'calendar' ? 'bg-primary text-primary-foreground' : 'text-slate-500 hover:text-slate-950'
            }`}
          >
            <Calendar className="h-4 w-4" />
            Calendar View
          </button>
          <button
            onClick={() => setActiveView('table')}
            className={`px-4 py-2 text-sm font-semibold flex items-center gap-1.5 transition-colors ${
              activeView === 'table' ? 'bg-primary text-primary-foreground' : 'text-slate-500 hover:text-slate-950'
            }`}
          >
            <Table className="h-4 w-4" />
            Table View
          </button>
        </div>

        {/* Inputs */}
        <div className="flex flex-wrap gap-3 items-center">
          <div className="relative max-w-xs">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              placeholder="Search sessions..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="pl-9 rounded-xl w-[200px]"
            />
          </div>

          <select
            value={filterStatus}
            onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}
            className="h-10 px-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
          >
            <option value="">All Statuses</option>
            <option value="Draft">Draft</option>
            <option value="Scheduled">Scheduled</option>
            <option value="Active">Active</option>
            <option value="Paused">Paused</option>
            <option value="Completed">Completed</option>
            <option value="Cancelled">Cancelled</option>
            <option value="Archived">Archived</option>
          </select>
        </div>
      </div>

      {/* CORE SESSIONS DIRECTORY CONTAINER */}
      {loading ? (
        <div className="flex h-60 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : error ? (
        <Card className="border-red-200 bg-red-50/50 dark:bg-red-950/20 dark:border-red-900">
          <CardContent className="flex items-center gap-3 p-6 text-red-800 dark:text-red-300">
            <ShieldAlert className="h-6 w-6" />
            <p className="font-semibold">{error}</p>
          </CardContent>
        </Card>
      ) : sessions.length === 0 ? (
        <Card className="border-2 border-dashed border-slate-200 dark:border-slate-800">
          <CardContent className="text-center py-16">
            <Calendar className="h-12 w-12 text-slate-350 dark:text-slate-650 mx-auto mb-4" />
            <p className="text-slate-600 dark:text-slate-400 font-semibold">No scheduled sessions found.</p>
            <p className="text-xs text-slate-400 mt-1">Try scheduling a session or adjusting search parameters.</p>
          </CardContent>
        </Card>
      ) : activeView === 'calendar' ? (
        // CALENDAR VIEW (Grouped by date grids)
        <div className="space-y-6">
          <div className="grid gap-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {sessions.map((session) => (
              <Card
                key={session.id}
                onClick={() => { fetchSessionDetails(session.id); setIsDetailModalOpen(true); }}
                className="cursor-pointer hover:shadow-lg transition-all duration-300 overflow-hidden border-slate-250 bg-white dark:border-slate-800 dark:bg-slate-900"
              >
                <div className="p-4 bg-slate-50/80 dark:bg-slate-950/30 border-b border-slate-100 dark:border-slate-800 flex justify-between items-center">
                  <span className="text-[10px] font-black uppercase tracking-wider text-slate-400">{session.session_type}</span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                    session.status === 'Active' ? 'bg-emerald-100 text-emerald-800 animate-pulse' :
                    session.status === 'Scheduled' ? 'bg-blue-100 text-blue-800' :
                    'bg-slate-100 text-slate-650'
                  }`}>
                    {session.status}
                  </span>
                </div>
                <CardContent className="p-4 space-y-3">
                  <h4 className="font-bold text-base text-slate-900 dark:text-white line-clamp-1">{session.name}</h4>
                  
                  <div className="space-y-1 text-xs text-slate-500">
                    <p className="flex items-center gap-1.5"><Calendar className="h-3.5 w-3.5 shrink-0 text-indigo-500" /> {session.date}</p>
                    <p className="flex items-center gap-1.5"><Clock className="h-3.5 w-3.5 shrink-0 text-amber-500" /> {session.start_time.slice(0,5)} - {session.end_time.slice(0,5)}</p>
                    {session.venue && (
                      <p className="flex items-center gap-1.5"><MapPin className="h-3.5 w-3.5 shrink-0 text-rose-500" /> {session.venue}</p>
                    )}
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800/80 text-[11px] font-semibold text-slate-400">
                    <span>Capacity: <b>{session.capacity || 'Unlimited'}</b></span>
                    <span>Assigned: <b>{session.assigned_members?.length || 0}</b></span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      ) : (
        // TABLE VIEW
        <Card className="border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-sm text-slate-650 dark:text-slate-400">
                <thead className="bg-slate-50 dark:bg-slate-900 text-slate-500 uppercase tracking-wider text-[11px] font-bold border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="p-4">Session Name</th>
                    <th className="p-4">Type</th>
                    <th className="p-4">Date</th>
                    <th className="p-4">Time Window</th>
                    <th className="p-4">Venue</th>
                    <th className="p-4">Roster</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-950/40">
                  {sessions.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/20 cursor-pointer" onClick={() => { fetchSessionDetails(s.id); setIsDetailModalOpen(true); }}>
                      <td className="p-4 font-bold text-slate-900 dark:text-white">{s.name}</td>
                      <td className="p-4 text-xs font-semibold">{s.session_type}</td>
                      <td className="p-4 text-xs">{s.date}</td>
                      <td className="p-4 text-xs">{s.start_time.slice(0,5)} - {s.end_time.slice(0,5)}</td>
                      <td className="p-4 text-xs">{s.venue || 'N/A'}</td>
                      <td className="p-4 text-xs font-bold text-primary">{s.assigned_members?.length || 0} assigned</td>
                      <td className="p-4">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          s.status === 'Active' ? 'bg-emerald-100 text-emerald-800' :
                          s.status === 'Scheduled' ? 'bg-blue-100 text-blue-800' :
                          'bg-slate-100 text-slate-650'
                        }`}>
                          {s.status}
                        </span>
                      </td>
                      <td className="p-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex justify-end gap-1.5">
                          {isCoordinatorOrAbove && s.status === 'Draft' && (
                            <Button size="sm" variant="destructive" onClick={() => handleDeleteSession(s.id)} className="h-8 w-8 p-0 rounded-lg">
                              <Trash className="h-3.5 w-3.5" />
                            </Button>
                          )}
                          {!isCoordinatorOrAbove && s.status === 'Active' && (
                            <Button size="sm" onClick={() => navigate(`/verify-attendance?session_id=${s.id}`)} className="h-8 rounded-lg">
                              Verify Check-In
                            </Button>
                          )}
                          {isCoordinatorOrAbove ? (
                            <Button size="sm" variant="outline" onClick={() => { fetchSessionDetails(s.id); setIsDetailModalOpen(true); }} className="h-8 rounded-lg">
                              Manage
                            </Button>
                          ) : (
                            s.status !== 'Active' && (
                              <span className="text-xs text-slate-400 font-medium">Session inactive</span>
                            )
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {/* PAGINATION */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between p-4 border-t border-slate-100 dark:border-slate-800">
                <span className="text-xs text-slate-500">Showing page {page} of {totalPages} ({totalCount} total)</span>
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="outline" disabled={page === 1} onClick={() => setPage(page - 1)} className="rounded-lg">Previous</Button>
                  <Button size="sm" variant="outline" disabled={page === totalPages} onClick={() => setPage(page + 1)} className="rounded-lg">Next</Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* SCHEDULE SESSION MODAL */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-xl rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900 animate-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Schedule Session</h3>
            <p className="text-xs text-slate-500 mb-6">Schedule a lecture, lab session, or corporate cohort meeting.</p>

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="sName">Session Title *</Label>
                  <Input id="sName" value={formName} onChange={(e) => setFormName(e.target.value)} required />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="sType">Session Type *</Label>
                  <select
                    id="sType"
                    value={formType}
                    onChange={(e) => setFormType(e.target.value)}
                    className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                  >
                    <option value="Lecture">Lecture</option>
                    <option value="Lab">Lab</option>
                    <option value="Workshop">Workshop</option>
                    <option value="Meeting">Meeting</option>
                    <option value="Seminar">Seminar</option>
                    <option value="Examination">Examination</option>
                    <option value="Training">Training</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="sDesc">Description</Label>
                <Input id="sDesc" value={formDesc} onChange={(e) => setFormDesc(e.target.value)} />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="sDate">Date *</Label>
                  <Input id="sDate" type="date" value={formDate} onChange={(e) => setFormDate(e.target.value)} required />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="sStart">Start Time *</Label>
                  <Input id="sStart" type="time" value={formStart} onChange={(e) => setFormStart(e.target.value)} required />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="sEnd">End Time *</Label>
                  <Input id="sEnd" type="time" value={formEnd} onChange={(e) => setFormEnd(e.target.value)} required />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="sGrace">Grace Time (mins)</Label>
                  <Input id="sGrace" type="number" value={formGrace} onChange={(e) => setFormGrace(Number(e.target.value))} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="sCapacity">Max Capacity</Label>
                  <Input id="sCapacity" type="number" placeholder="No limit" value={formCapacity} onChange={(e) => setFormCapacity(e.target.value ? Number(e.target.value) : '')} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="sEvidence">Verification Mode</Label>
                  <select
                    id="sEvidence"
                    value={formEvidence}
                    onChange={(e) => setFormEvidence(e.target.value)}
                    className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                  >
                    <option value="GPS">GPS Only</option>
                    <option value="Face">Face Only</option>
                    <option value="QR">QR Only</option>
                    <option value="Manual">Manual Override</option>
                    <option value="Hybrid">Hybrid Check-In</option>
                  </select>
                </div>
              </div>

              <div className="rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 p-4 space-y-3">
                <p className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1"><MapPin className="h-3.5 w-3.5 text-rose-500" /> GPS Geofence Configuration</p>
                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <Label className="text-[10px]" htmlFor="sLat">Latitude</Label>
                    <Input id="sLat" type="number" step="any" placeholder="e.g. 12.9716" value={formLat} onChange={(e) => setFormLat(e.target.value ? Number(e.target.value) : '')} />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-[10px]" htmlFor="sLon">Longitude</Label>
                    <Input id="sLon" type="number" step="any" placeholder="e.g. 77.5946" value={formLon} onChange={(e) => setFormLon(e.target.value ? Number(e.target.value) : '')} />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-[10px]" htmlFor="sRad">Radius (meters)</Label>
                    <Input id="sRad" type="number" value={formGpsRadius} onChange={(e) => setFormGpsRadius(Number(e.target.value))} />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="sOrg">Organization Scope *</Label>
                  <select
                    id="sOrg"
                    value={formOrgId}
                    onChange={(e) => setFormOrgId(Number(e.target.value) || '')}
                    className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                    required
                    disabled={user?.role !== 'SystemAdmin'}
                  >
                    <option value="">Select Org...</option>
                    {orgs.map((o) => (
                      <option key={o.id} value={o.id}>{o.name}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="sDept">Department</Label>
                  <select
                    id="sDept"
                    value={formDeptId}
                    onChange={(e) => setFormDeptId(Number(e.target.value) || '')}
                    className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                  >
                    <option value="">All Departments</option>
                    {depts.map((d) => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <Button type="button" variant="outline" onClick={() => setIsCreateModalOpen(false)} disabled={submitting}>
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting} className="gap-2">
                  {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                  Schedule
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* SESSION DETAIL DRAWER / OVERLAY */}
      {isDetailModalOpen && selectedSession && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/45 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-2xl h-screen bg-white dark:bg-slate-900 shadow-2xl p-6 overflow-y-auto flex flex-col justify-between animate-in slide-in-from-right duration-350">
            <div>
              {/* Header */}
              <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800 mb-6">
                <div>
                  <h3 className="text-xl font-black text-slate-950 dark:text-white">{selectedSession.name}</h3>
                  <span className="text-xs text-slate-400">ID: {selectedSession.id} | Status: <b>{selectedSession.status}</b></span>
                </div>
                <button className="text-xl font-bold opacity-60 hover:opacity-100" onClick={() => setIsDetailModalOpen(false)}>×</button>
              </div>

              {/* State Transition buttons */}
              {isCoordinatorOrAbove && (
                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-950/20 border border-slate-100 dark:border-slate-800 mb-6">
                  <h5 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Governance Console</h5>
                  <div className="flex flex-wrap gap-2">
                    {selectedSession.status === 'Draft' && (
                      <Button size="sm" onClick={() => handleTransitionState(selectedSession.id, 'Scheduled')} className="gap-1.5"><Play className="h-3.5 w-3.5" /> Publish</Button>
                    )}
                    {selectedSession.status === 'Scheduled' && (
                      <Button size="sm" onClick={() => handleTransitionState(selectedSession.id, 'Active')} className="gap-1.5"><Play className="h-3.5 w-3.5" /> Start Window</Button>
                    )}
                    {selectedSession.status === 'Active' && (
                      <>
                        <Button size="sm" variant="outline" onClick={() => handleTransitionState(selectedSession.id, 'Paused')} className="gap-1.5"><Pause className="h-3.5 w-3.5" /> Pause</Button>
                        <Button size="sm" onClick={() => handleTransitionState(selectedSession.id, 'Completed')} className="gap-1.5"><CheckCircle className="h-3.5 w-3.5" /> Complete</Button>
                      </>
                    )}
                    {selectedSession.status === 'Paused' && (
                      <>
                        <Button size="sm" onClick={() => handleTransitionState(selectedSession.id, 'Active')} className="gap-1.5"><Play className="h-3.5 w-3.5" /> Resume</Button>
                        <Button size="sm" onClick={() => handleTransitionState(selectedSession.id, 'Completed')} className="gap-1.5"><CheckCircle className="h-3.5 w-3.5" /> Complete</Button>
                      </>
                    )}
                    {(selectedSession.status === 'Draft' || selectedSession.status === 'Scheduled') && (
                      <Button size="sm" variant="destructive" onClick={() => handleTransitionState(selectedSession.id, 'Cancelled')} className="gap-1.5"><XCircle className="h-3.5 w-3.5" /> Cancel</Button>
                    )}
                    {(selectedSession.status === 'Completed' || selectedSession.status === 'Cancelled') && (
                      <Button size="sm" variant="outline" onClick={() => handleTransitionState(selectedSession.id, 'Archived')} className="gap-1.5"><Archive className="h-3.5 w-3.5" /> Archive</Button>
                    )}
                  </div>
                </div>
              )}

              {/* Roster & Participant Scope */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                    <Users className="h-4 w-4 text-primary" /> Roster Directory ({selectedSession.assigned_members?.length || 0} assigned)
                  </h4>
                  {isCoordinatorOrAbove && selectedSession.status === 'Draft' && (
                    <Button size="sm" onClick={() => { setIsAssignModalOpen(true); setSelectedUserIds([]); }} className="gap-1 rounded-lg">
                      <UserPlus className="h-3.5 w-3.5" /> Assign Members
                    </Button>
                  )}
                </div>

                {/* Assigned List */}
                <div className="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden divide-y divide-slate-100 dark:divide-slate-800 max-h-56 overflow-y-auto">
                  {selectedSession.assigned_members?.length === 0 ? (
                    <p className="p-4 text-xs text-slate-500 text-center">No participants assigned to this roster.</p>
                  ) : (
                    selectedSession.assigned_members?.map((m) => (
                      <div key={m.id} className="p-3 flex items-center justify-between text-xs hover:bg-slate-50/40">
                        <div>
                          <p className="font-bold text-slate-900 dark:text-white">{m.full_name}</p>
                          <p className="text-[10px] text-slate-400">{m.email} | {m.role}</p>
                        </div>
                        {isCoordinatorOrAbove && selectedSession.status === 'Draft' && (
                          <button onClick={() => handleRemoveMember(m.id)} className="text-red-500 hover:text-red-700">
                            <Trash className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Manual Attendance Override Console */}
              {isCoordinatorOrAbove && selectedSession.status !== 'Draft' && (
                <form onSubmit={handleManualAttendance} className="mt-6 border-t border-slate-100 dark:border-slate-800 pt-6 space-y-3">
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                    <Award className="h-4 w-4 text-indigo-500" /> Manual Attendance Override
                  </h4>
                  <div className="flex gap-3 items-end">
                    <div className="flex-1 space-y-1">
                      <Label className="text-[10px]">Select Participant</Label>
                      <select
                        value={manualMemberId}
                        onChange={(e) => setManualMemberId(Number(e.target.value) || '')}
                        className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs"
                        required
                      >
                        <option value="">Select User...</option>
                        {selectedSession.assigned_members?.map((m) => (
                          <option key={m.id} value={m.id}>{m.full_name}</option>
                        ))}
                      </select>
                    </div>
                    <div className="w-32 space-y-1">
                      <Label className="text-[10px]">Mark Status</Label>
                      <select
                        value={manualStatus}
                        onChange={(e) => setManualStatus(e.target.value)}
                        className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs"
                      >
                        <option value="Present">Present</option>
                        <option value="Late">Late</option>
                        <option value="Absent">Absent</option>
                        <option value="Excused">Excused</option>
                      </select>
                    </div>
                    <Button type="submit" className="h-10 rounded-lg">Override</Button>
                  </div>
                </form>
              )}

              {/* Live Attendance check-ins review log */}
              {selectedSession.status !== 'Draft' && (
                <div className="mt-6 border-t border-slate-100 dark:border-slate-800 pt-6 space-y-3">
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                    <ShieldCheck className="h-4 w-4 text-emerald-500" /> Live Verification Stream
                  </h4>
                  <div className="rounded-xl border border-slate-200 dark:border-slate-800 max-h-48 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800 text-xs">
                    {sessionAttendances.length === 0 ? (
                      <p className="p-4 text-center text-slate-500">No active check-in streams recorded yet.</p>
                    ) : (
                      sessionAttendances.map((att) => (
                        <div key={att.id} className="p-3 flex items-center justify-between hover:bg-slate-50/40">
                          <div>
                            <span className="font-semibold text-slate-800 dark:text-slate-200">{att.member?.full_name}</span>
                            <span className="mx-2 text-slate-400">|</span>
                            <span className="text-[10px] text-slate-400">In: {att.check_in_time ? new Date(att.check_in_time).toLocaleTimeString() : 'N/A'}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
                              att.status === 'Present' ? 'bg-emerald-100 text-emerald-800' :
                              att.status === 'Late' ? 'bg-amber-100 text-amber-800' :
                              att.status === 'Excused' ? 'bg-indigo-100 text-indigo-800' :
                              att.status === 'Pending Approval' ? 'bg-amber-100 text-amber-850 animate-pulse' :
                              'bg-red-100 text-red-800'
                            }`}>{att.status}</span>
                            {isCoordinatorOrAbove && att.status === 'Pending Approval' && (
                              <button
                                onClick={async (e) => {
                                  e.stopPropagation();
                                  try {
                                    await api.post(`/sessions/${selectedSession.id}/approve-attendance?member_id=${att.member_id}`);
                                    addToast('Check-in successfully approved.', 'success');
                                    fetchSessionDetails(selectedSession.id);
                                  } catch (err: any) {
                                    addToast(err.response?.data?.message || 'Approval failed.', 'error');
                                  }
                                }}
                                className="h-6 px-2 text-[10px] rounded-md bg-emerald-600 hover:bg-emerald-700 text-white font-bold transition-colors"
                              >
                                Approve
                              </button>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Bottom Actions */}
            <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex justify-end gap-3 mt-6 shrink-0">
              {!isCoordinatorOrAbove && selectedSession.status === 'Active' && (
                <Button onClick={() => { setIsDetailModalOpen(false); navigate(`/verify-attendance?session_id=${selectedSession.id}`); }} className="font-bold">
                  Verify Check-In
                </Button>
              )}
              <Button variant="outline" onClick={() => setIsDetailModalOpen(false)}>Close Control drawer</Button>
            </div>
          </div>
        </div>
      )}

      {/* ROSTER BULK ASSIGN SUB-MODAL */}
      {isAssignModalOpen && selectedSession && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900 animate-in zoom-in-95 duration-200 max-h-[80vh] flex flex-col justify-between">
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Assign Participants</h3>
              <p className="text-xs text-slate-500 mb-4">Select users from your tenant bounds to add to the roster.</p>
              
              {/* User Selection Checkbox list */}
              <div className="border rounded-xl divide-y divide-slate-100 max-h-60 overflow-y-auto p-2 bg-slate-50/50">
                {allUsers
                  .filter((u) => !selectedSession.assigned_members?.some((am) => am.id === u.id))
                  .map((u) => (
                    <label key={u.id} className="flex items-center gap-3 p-2.5 hover:bg-slate-100 cursor-pointer rounded-lg text-xs font-semibold">
                      <input
                        type="checkbox"
                        checked={selectedUserIds.includes(u.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedUserIds([...selectedUserIds, u.id]);
                          } else {
                            setSelectedUserIds(selectedUserIds.filter((id) => id !== u.id));
                          }
                        }}
                      />
                      <div>
                        <p className="text-slate-850 font-bold">{u.full_name}</p>
                        <p className="text-[10px] text-slate-400">{u.email} | {u.role}</p>
                      </div>
                    </label>
                  ))}
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800 mt-4 shrink-0">
              <Button variant="outline" onClick={() => setIsAssignModalOpen(false)}>Cancel</Button>
              <Button onClick={handleBulkAssign} disabled={selectedUserIds.length === 0}>Add Selection</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
