import React, { useState, useEffect } from 'react';
import api from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Briefcase, Users, Plus, Edit2, Trash2, Search, Loader2, User, ShieldAlert, Award } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToastStore } from '@/store/toastStore';
import { useAuthStore } from '@/store/authStore';

interface SimpleUser {
  id: number;
  full_name: string;
  email: string;
  role: string;
}

interface SimpleOrg {
  id: number;
  name: string;
}

interface Department {
  id: number;
  name: string;
  description?: string;
  organization_id: number;
  head_id?: number;
  coordinator_id?: number;
  status: string;
  head?: { id: number; full_name: string; email: string };
  coordinator?: { id: number; full_name: string; email: string };
}

interface Team {
  id: number;
  name: string;
  department_id: number;
  leader_id?: number;
  status: string;
  leader?: { id: number; full_name: string; email: string };
  department?: { id: number; name: string };
}

export default function DepartmentsPage() {
  const { user } = useAuthStore();
  const { addToast } = useToastStore();
  
  // Tab switcher state
  const [activeTab, setActiveTab] = useState<'departments' | 'teams'>('departments');

  // Lists
  const [depts, setDepts] = useState<Department[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [orgs, setOrgs] = useState<SimpleOrg[]>([]);
  const [usersList, setUsersList] = useState<SimpleUser[]>([]);

  // Page States
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const limit = 10;

  // Modals
  const [isDeptModalOpen, setIsDeptModalOpen] = useState(false);
  const [isTeamModalOpen, setIsTeamModalOpen] = useState(false);
  const [editingDept, setEditingDept] = useState<Department | null>(null);
  const [editingTeam, setEditingTeam] = useState<Team | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Department Form Fields
  const [deptName, setDeptName] = useState('');
  const [deptDesc, setDeptDesc] = useState('');
  const [deptOrgId, setDeptOrgId] = useState<number | ''>('');
  const [deptHeadId, setDeptHeadId] = useState<number | ''>('');
  const [deptCoordId, setDeptCoordId] = useState<number | ''>('');
  const [deptStatus, setDeptStatus] = useState('Active');

  // Team Form Fields
  const [teamName, setTeamName] = useState('');
  const [teamDeptId, setTeamDeptId] = useState<number | ''>('');
  const [teamLeaderId, setTeamLeaderId] = useState<number | ''>('');
  const [teamStatus, setTeamStatus] = useState('Active');

  // Load auxiliary selection directories (Orgs, Users, Depts)
  const loadSelectionHelpers = async () => {
    try {
      const orgsRes = await api.get('/organizations/?limit=100');
      if (orgsRes.data?.success) setOrgs(orgsRes.data.data || []);

      const usersRes = await api.get('/users/?limit=100');
      if (usersRes.data?.success) setUsersList(usersRes.data.data || []);
    } catch {
      // Fail silently for helper loads
    }
  };

  const fetchDepartments = async () => {
    setLoading(true);
    setError(null);
    try {
      const skip = (page - 1) * limit;
      const res = await api.get(`/departments/?skip=${skip}&limit=${limit}&q=${search}`);
      if (res.data?.success) {
        setDepts(res.data.data || []);
        const msg = res.data.message || '';
        const match = msg.match(/Total: (\d+)/);
        setTotalCount(match ? parseInt(match[1]) : (res.data.data?.length || 0));
      } else {
        setError('Failed to fetch departments.');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred loading departments.');
    } finally {
      setLoading(false);
    }
  };

  const fetchTeams = async () => {
    setLoading(true);
    setError(null);
    try {
      const skip = (page - 1) * limit;
      const res = await api.get(`/teams/?skip=${skip}&limit=${limit}&q=${search}`);
      if (res.data?.success) {
        setTeams(res.data.data || []);
        const msg = res.data.message || '';
        const match = msg.match(/Total: (\d+)/);
        setTotalCount(match ? parseInt(match[1]) : (res.data.data?.length || 0));
      } else {
        setError('Failed to fetch teams.');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred loading teams.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSelectionHelpers();
  }, []);

  useEffect(() => {
    if (activeTab === 'departments') {
      fetchDepartments();
    } else {
      fetchTeams();
    }
  }, [activeTab, search, page]);

  // Dept modal operations
  const openCreateDeptModal = () => {
    setEditingDept(null);
    setDeptName('');
    setDeptDesc('');
    setDeptOrgId(user?.organization_id || '');
    setDeptHeadId('');
    setDeptCoordId('');
    setDeptStatus('Active');
    setIsDeptModalOpen(true);
  };

  const openEditDeptModal = (dept: Department) => {
    setEditingDept(dept);
    setDeptName(dept.name);
    setDeptDesc(dept.description || '');
    setDeptOrgId(dept.organization_id);
    setDeptHeadId(dept.head_id || '');
    setDeptCoordId(dept.coordinator_id || '');
    setDeptStatus(dept.status);
    setIsDeptModalOpen(true);
  };

  // Team modal operations
  const openCreateTeamModal = () => {
    setEditingTeam(null);
    setTeamName('');
    setTeamDeptId('');
    setTeamLeaderId('');
    setTeamStatus('Active');
    setIsTeamModalOpen(true);
  };

  const openEditTeamModal = (t: Team) => {
    setEditingTeam(t);
    setTeamName(t.name);
    setTeamDeptId(t.department_id);
    setTeamLeaderId(t.leader_id || '');
    setTeamStatus(t.status);
    setIsTeamModalOpen(true);
  };

  const handleDeptSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deptName.trim() || !deptOrgId) {
      addToast('Department name and organization are required.', 'error');
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        name: deptName,
        description: deptDesc || null,
        organization_id: Number(deptOrgId),
        head_id: deptHeadId ? Number(deptHeadId) : null,
        coordinator_id: deptCoordId ? Number(deptCoordId) : null,
        status: deptStatus
      };

      if (editingDept) {
        await api.put(`/departments/${editingDept.id}`, payload);
        addToast('Department updated successfully.', 'success');
      } else {
        await api.post('/departments/', payload);
        addToast('Department registered successfully.', 'success');
      }
      setIsDeptModalOpen(false);
      fetchDepartments();
    } catch (err: any) {
      const errMsg = err.response?.data?.errors?.[0]?.detail || err.response?.data?.message || 'Department request failed.';
      addToast(errMsg, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleTeamSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!teamName.trim() || !teamDeptId) {
      addToast('Team name and department selection are required.', 'error');
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        name: teamName,
        department_id: Number(teamDeptId),
        leader_id: teamLeaderId ? Number(teamLeaderId) : null,
        status: teamStatus
      };

      if (editingTeam) {
        await api.put(`/teams/${editingTeam.id}`, payload);
        addToast('Team updated successfully.', 'success');
      } else {
        await api.post('/teams/', payload);
        addToast('Team registered successfully.', 'success');
      }
      setIsTeamModalOpen(false);
      fetchTeams();
    } catch (err: any) {
      const errMsg = err.response?.data?.errors?.[0]?.detail || err.response?.data?.message || 'Team request failed.';
      addToast(errMsg, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeptDeactivate = async (id: number) => {
    if (!confirm('Are you sure you want to deactivate this department?')) return;
    try {
      await api.delete(`/departments/${id}`);
      addToast('Department deactivated.', 'success');
      fetchDepartments();
    } catch (err: any) {
      addToast('Failed to deactivate department.', 'error');
    }
  };

  const handleTeamDeactivate = async (id: number) => {
    if (!confirm('Are you sure you want to deactivate this team?')) return;
    try {
      await api.delete(`/teams/${id}`);
      addToast('Team deactivated.', 'success');
      fetchTeams();
    } catch (err: any) {
      addToast('Failed to deactivate team.', 'error');
    }
  };

  const isSystemOrOrgAdmin = user?.role === 'SystemAdmin' || user?.role === 'OrgAdmin';
  const totalPages = Math.ceil(totalCount / limit);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Directories
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Configure functional departments, active teams, and administrator bounds.
          </p>
        </div>

        {/* Action Button based on active tab */}
        {isSystemOrOrgAdmin && (
          activeTab === 'departments' ? (
            <Button onClick={openCreateDeptModal} className="gap-2 rounded-xl">
              <Plus className="h-4 w-4" />
              Add Department
            </Button>
          ) : (
            <Button onClick={openCreateTeamModal} className="gap-2 rounded-xl">
              <Plus className="h-4 w-4" />
              Add Team
            </Button>
          )
        )}
      </div>

      {/* TAB SELECTOR */}
      <div className="flex border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => { setActiveTab('departments'); setPage(1); setSearch(''); }}
          className={`px-6 py-3 text-sm font-bold border-b-2 transition-all ${
            activeTab === 'departments'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          Departments
        </button>
        <button
          onClick={() => { setActiveTab('teams'); setPage(1); setSearch(''); }}
          className={`px-6 py-3 text-sm font-bold border-b-2 transition-all ${
            activeTab === 'teams'
              ? 'border-primary text-primary'
              : 'border-transparent text-slate-500 hover:text-slate-900'
          }`}
        >
          Teams
        </button>
      </div>

      {/* SEARCH QUERY */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <Input
          placeholder={activeTab === 'departments' ? 'Search departments...' : 'Search teams...'}
          className="pl-9 rounded-xl border-slate-200 dark:border-slate-800"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
      </div>

      {/* CORE DIRECTORY VIEW */}
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
      ) : activeTab === 'departments' ? (
        depts.length === 0 ? (
          <Card className="border-2 border-dashed border-slate-200 dark:border-slate-800">
            <CardContent className="text-center py-16">
              <Briefcase className="h-12 w-12 text-slate-350 dark:text-slate-650 mx-auto mb-4" />
              <p className="text-slate-600 dark:text-slate-400 font-semibold">No departments found.</p>
              <p className="text-xs text-slate-400 mt-1">Configure functional entities to allocate students/faculty.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {depts.map((d) => (
                <Card key={d.id} className="overflow-hidden hover:shadow-lg transition-all duration-300 border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
                  <CardHeader className="bg-slate-50/30 dark:bg-slate-950/10 pb-4 border-b border-slate-100 dark:border-slate-800/40">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
                          <Briefcase className="h-5 w-5" />
                        </div>
                        <div>
                          <CardTitle className="text-base font-bold text-slate-900 dark:text-white">{d.name}</CardTitle>
                          <CardDescription className="text-xs">Org ID: {d.organization_id}</CardDescription>
                        </div>
                      </div>
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${d.status === 'Active' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'}`}>
                        {d.status}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent className="p-5 space-y-4 text-sm text-slate-600 dark:text-slate-400">
                    <p className="text-xs text-slate-500 line-clamp-2">{d.description || 'No description configured.'}</p>
                    
                    <div className="space-y-2 pt-3 border-t border-slate-100 dark:border-slate-800/40">
                      <div className="flex items-center gap-2 text-xs">
                        <Award className="h-3.5 w-3.5 text-indigo-500" />
                        <span>Head: <b>{d.head?.full_name || 'Not assigned'}</b></span>
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        <User className="h-3.5 w-3.5 text-amber-500" />
                        <span>Coordinator: <b>{d.coordinator?.full_name || 'Not assigned'}</b></span>
                      </div>
                    </div>

                    {isSystemOrOrgAdmin && (
                      <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800/40">
                        <Button onClick={() => openEditDeptModal(d)} size="sm" variant="outline" className="gap-1 rounded-lg">
                          <Edit2 className="h-3.5 w-3.5" />
                          Edit
                        </Button>
                        <Button onClick={() => handleDeptDeactivate(d.id)} size="sm" variant="destructive" className="gap-1 rounded-lg" disabled={d.status === 'Inactive'}>
                          <Trash2 className="h-3.5 w-3.5" />
                          Deactivate
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* PAGINATION */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between pt-4">
                <span className="text-xs text-slate-500">Showing page {page} of {totalPages} ({totalCount} total)</span>
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="outline" disabled={page === 1} onClick={() => setPage(page - 1)} className="rounded-lg">Previous</Button>
                  <Button size="sm" variant="outline" disabled={page === totalPages} onClick={() => setPage(page + 1)} className="rounded-lg">Next</Button>
                </div>
              </div>
            )}
          </div>
        )
      ) : (
        // TEAMS ACTIVE TAB
        teams.length === 0 ? (
          <Card className="border-2 border-dashed border-slate-200 dark:border-slate-800">
            <CardContent className="text-center py-16">
              <Users className="h-12 w-12 text-slate-350 dark:text-slate-650 mx-auto mb-4" />
              <p className="text-slate-600 dark:text-slate-400 font-semibold">No teams found.</p>
              <p className="text-xs text-slate-400 mt-1">Teams group class cohorts or structural personnel projects.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {teams.map((t) => (
                <Card key={t.id} className="overflow-hidden hover:shadow-lg transition-all duration-300 border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
                  <CardHeader className="bg-slate-50/30 dark:bg-slate-950/10 pb-4 border-b border-slate-100 dark:border-slate-800/40">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
                          <Users className="h-5 w-5" />
                        </div>
                        <div>
                          <CardTitle className="text-base font-bold text-slate-900 dark:text-white">{t.name}</CardTitle>
                          <CardDescription className="text-xs">Dept: {t.department?.name || 'Unassigned'}</CardDescription>
                        </div>
                      </div>
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${t.status === 'Active' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'}`}>
                        {t.status}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent className="p-5 space-y-4 text-sm text-slate-600 dark:text-slate-400">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-xs">
                        <Award className="h-3.5 w-3.5 text-primary" />
                        <span>Leader: <b>{t.leader?.full_name || 'Not assigned'}</b></span>
                      </div>
                    </div>

                    {isSystemOrOrgAdmin && (
                      <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800/40">
                        <Button onClick={() => openEditTeamModal(t)} size="sm" variant="outline" className="gap-1 rounded-lg">
                          <Edit2 className="h-3.5 w-3.5" />
                          Edit
                        </Button>
                        <Button onClick={() => handleTeamDeactivate(t.id)} size="sm" variant="destructive" className="gap-1 rounded-lg" disabled={t.status === 'Inactive'}>
                          <Trash2 className="h-3.5 w-3.5" />
                          Deactivate
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* PAGINATION */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between pt-4">
                <span className="text-xs text-slate-500">Showing page {page} of {totalPages} ({totalCount} total)</span>
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="outline" disabled={page === 1} onClick={() => setPage(page - 1)} className="rounded-lg">Previous</Button>
                  <Button size="sm" variant="outline" disabled={page === totalPages} onClick={() => setPage(page + 1)} className="rounded-lg">Next</Button>
                </div>
              </div>
            )}
          </div>
        )
      )}

      {/* DEPARTMENT MODAL */}
      {isDeptModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900 animate-in zoom-in-95 duration-200">
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
              {editingDept ? 'Edit Department' : 'Create Department'}
            </h3>
            <p className="text-xs text-slate-500 mb-6">
              Establish administrative department fields.
            </p>

            <form onSubmit={handleDeptSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="deptName">Department Name *</Label>
                <Input
                  id="deptName"
                  value={deptName}
                  onChange={(e) => setDeptName(e.target.value)}
                  placeholder="e.g. Computer Science"
                  required
                  disabled={submitting}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="deptDesc">Description</Label>
                <Input
                  id="deptDesc"
                  value={deptDesc}
                  onChange={(e) => setDeptDesc(e.target.value)}
                  placeholder="Brief description details"
                  disabled={submitting}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="deptOrg">Organization Assignment *</Label>
                <select
                  id="deptOrg"
                  value={deptOrgId}
                  onChange={(e) => setDeptOrgId(Number(e.target.value) || '')}
                  className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                  required
                  disabled={submitting || !isSystemOrOrgAdmin}
                >
                  <option value="">Select Organization...</option>
                  {orgs.map((o) => (
                    <option key={o.id} value={o.id}>{o.name}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="deptHead">Department Head</Label>
                  <select
                    id="deptHead"
                    value={deptHeadId}
                    onChange={(e) => setDeptHeadId(Number(e.target.value) || '')}
                    className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                    disabled={submitting}
                  >
                    <option value="">None</option>
                    {usersList.map((u) => (
                      <option key={u.id} value={u.id}>{u.full_name} ({u.role})</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="deptCoord">Coordinator</Label>
                  <select
                    id="deptCoord"
                    value={deptCoordId}
                    onChange={(e) => setDeptCoordId(Number(e.target.value) || '')}
                    className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                    disabled={submitting}
                  >
                    <option value="">None</option>
                    {usersList.map((u) => (
                      <option key={u.id} value={u.id}>{u.full_name} ({u.role})</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="deptStatus">Status</Label>
                <select
                  id="deptStatus"
                  value={deptStatus}
                  onChange={(e) => setDeptStatus(e.target.value)}
                  className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                  disabled={submitting}
                >
                  <option value="Active">Active</option>
                  <option value="Inactive">Inactive</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <Button type="button" variant="outline" onClick={() => setIsDeptModalOpen(false)} disabled={submitting} className="rounded-lg">
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting} className="rounded-lg gap-2">
                  {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                  {editingDept ? 'Save Changes' : 'Create'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* TEAM MODAL */}
      {isTeamModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900 animate-in zoom-in-95 duration-200">
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
              {editingTeam ? 'Edit Team' : 'Create Team'}
            </h3>
            <p className="text-xs text-slate-500 mb-6">
              Establish structural team cohorts.
            </p>

            <form onSubmit={handleTeamSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="teamName">Team Name *</Label>
                <Input
                  id="teamName"
                  value={teamName}
                  onChange={(e) => setTeamName(e.target.value)}
                  placeholder="e.g. Engineering Alpha"
                  required
                  disabled={submitting}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="teamDept">Department Assignment *</Label>
                <select
                  id="teamDept"
                  value={teamDeptId}
                  onChange={(e) => setTeamDeptId(Number(e.target.value) || '')}
                  className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                  required
                  disabled={submitting}
                >
                  <option value="">Select Department...</option>
                  {depts.map((d) => (
                    <option key={d.id} value={d.id}>{d.name} (Org: {d.organization_id})</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="teamLeader">Team Leader</Label>
                <select
                  id="teamLeader"
                  value={teamLeaderId}
                  onChange={(e) => setTeamLeaderId(Number(e.target.value) || '')}
                  className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                  disabled={submitting}
                >
                  <option value="">None</option>
                  {usersList.map((u) => (
                    <option key={u.id} value={u.id}>{u.full_name} ({u.role})</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="teamStatus">Status</Label>
                <select
                  id="teamStatus"
                  value={teamStatus}
                  onChange={(e) => setTeamStatus(e.target.value)}
                  className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                  disabled={submitting}
                >
                  <option value="Active">Active</option>
                  <option value="Inactive">Inactive</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <Button type="button" variant="outline" onClick={() => setIsTeamModalOpen(false)} disabled={submitting} className="rounded-lg">
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting} className="rounded-lg gap-2">
                  {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                  {editingTeam ? 'Save Changes' : 'Create'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
