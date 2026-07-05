import React, { useState, useEffect } from 'react';
import api from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, Plus, Edit2, ShieldAlert, Search, Loader2, UserCheck, UserMinus, Shield, Phone, Mail, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToastStore } from '@/store/toastStore';
import { useAuthStore } from '@/store/authStore';

interface SimpleRef {
  id: number;
  name: string;
}

interface Member {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  phone?: string;
  gender?: string;
  organization_id?: number;
  department_id?: number;
  team_id?: number;
  emergency_contact?: string;
  joining_date?: string;
  status: string;
  created_at: string;
  organization?: SimpleRef;
  department?: SimpleRef;
  team?: SimpleRef;
}

export default function MembersPage() {
  const { user } = useAuthStore();
  const { addToast } = useToastStore();

  // Lists
  const [members, setMembers] = useState<Member[]>([]);
  const [orgs, setOrgs] = useState<SimpleRef[]>([]);
  const [depts, setDepts] = useState<SimpleRef[]>([]);
  const [teams, setTeams] = useState<SimpleRef[]>([]);

  // Page States
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Search, Filters & Pagination
  const [search, setSearch] = useState('');
  const [filterOrg, setFilterOrg] = useState<string>('');
  const [filterDept, setFilterDept] = useState<string>('');
  const [filterTeam, setFilterTeam] = useState<string>('');
  const [filterRole, setFilterRole] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const limit = 8;

  // Modals
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingMember, setEditingMember] = useState<Member | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form Fields
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('Student');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [gender, setGender] = useState('Male');
  const [orgId, setOrgId] = useState<number | ''>('');
  const [deptId, setDeptId] = useState<number | ''>('');
  const [teamId, setTeamId] = useState<number | ''>('');
  const [emergencyContact, setEmergencyContact] = useState('');
  const [joiningDate, setJoiningDate] = useState('');
  const [statusVal, setStatusVal] = useState('Active');

  const loadFilterHelpers = async () => {
    try {
      const orgsRes = await api.get('/organizations/?limit=100');
      if (orgsRes.data?.success) setOrgs(orgsRes.data.data || []);

      const deptsRes = await api.get('/departments/?limit=100');
      if (deptsRes.data?.success) setDepts(deptsRes.data.data || []);

      const teamsRes = await api.get('/teams/?limit=100');
      if (teamsRes.data?.success) setTeams(teamsRes.data.data || []);
    } catch {
      // Fail silently
    }
  };

  const fetchMembers = async () => {
    setLoading(true);
    setError(null);
    try {
      const skip = (page - 1) * limit;
      let queryStr = `/users/?skip=${skip}&limit=${limit}&q=${search}`;
      
      if (filterOrg) queryStr += `&organization_id=${filterOrg}`;
      if (filterDept) queryStr += `&department_id=${filterDept}`;
      if (filterTeam) queryStr += `&team_id=${filterTeam}`;
      if (filterRole) queryStr += `&role=${filterRole}`;
      if (filterStatus) queryStr += `&status=${filterStatus}`;

      const res = await api.get(queryStr);
      if (res.data?.success) {
        setMembers(res.data.data || []);
        const msg = res.data.message || '';
        const match = msg.match(/Total: (\d+)/);
        setTotalCount(match ? parseInt(match[1]) : (res.data.data?.length || 0));
      } else {
        setError('Failed to fetch user directory.');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred loading users.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFilterHelpers();
  }, []);

  useEffect(() => {
    fetchMembers();
  }, [search, filterOrg, filterDept, filterTeam, filterRole, filterStatus, page]);

  const openCreateModal = () => {
    setEditingMember(null);
    setEmail('');
    setFullName('');
    setRole('Student');
    setPassword('');
    setPhone('');
    setGender('Male');
    setOrgId(user?.organization_id || '');
    setDeptId('');
    setTeamId('');
    setEmergencyContact('');
    setJoiningDate(new Date().toISOString().split('T')[0]);
    setStatusVal('Active');
    setIsModalOpen(true);
  };

  const openEditModal = (m: Member) => {
    setEditingMember(m);
    setEmail(m.email);
    setFullName(m.full_name);
    setRole(m.role);
    setPassword(''); // Never prefill password
    setPhone(m.phone || '');
    setGender(m.gender || 'Male');
    setOrgId(m.organization_id || '');
    setDeptId(m.department_id || '');
    setTeamId(m.team_id || '');
    setEmergencyContact(m.emergency_contact || '');
    setJoiningDate(m.joining_date || '');
    setStatusVal(m.status);
    setIsModalOpen(true);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !fullName) {
      addToast('Full name and email are required.', 'error');
      return;
    }
    if (!editingMember && !password) {
      addToast('Password is required for new users.', 'error');
      return;
    }

    setSubmitting(true);
    try {
      const payload: any = {
        email,
        full_name: fullName,
        role,
        phone: phone || null,
        gender,
        organization_id: orgId ? Number(orgId) : null,
        department_id: deptId ? Number(deptId) : null,
        team_id: teamId ? Number(teamId) : null,
        emergency_contact: emergencyContact || null,
        joining_date: joiningDate || null,
        status: statusVal
      };

      if (password) {
        payload.password = password;
      }

      if (editingMember) {
        await api.put(`/users/${editingMember.id}`, payload);
        addToast('Member profile updated successfully.', 'success');
      } else {
        await api.post('/users/', payload);
        addToast('Member account created successfully.', 'success');
      }
      setIsModalOpen(false);
      fetchMembers();
    } catch (err: any) {
      const errMsg = err.response?.data?.errors?.[0]?.detail || err.response?.data?.message || 'Member request failed.';
      addToast(errMsg, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleActivationToggle = async (m: Member) => {
    const isActivating = !m.is_active;
    try {
      if (isActivating) {
        await api.post(`/users/${m.id}/activate`);
        addToast(`Member ${m.full_name} has been activated.`, 'success');
      } else {
        await api.delete(`/users/${m.id}`);
        addToast(`Member ${m.full_name} has been deactivated.`, 'success');
      }
      fetchMembers();
    } catch {
      addToast('Failed to change member status.', 'error');
    }
  };

  const isSystemOrOrgAdmin = user?.role === 'SystemAdmin' || user?.role === 'OrgAdmin';
  const totalPages = Math.ceil(totalCount / limit);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Members
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Manage employee roles, student profiles, and administrative roster registries.
          </p>
        </div>
        {isSystemOrOrgAdmin && (
          <Button onClick={openCreateModal} className="gap-2 rounded-xl">
            <Plus className="h-4 w-4" />
            Add Member
          </Button>
        )}
      </div>

      {/* FILTER CONTROLS BAR */}
      <Card className="border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm rounded-2xl">
        <CardContent className="p-4 grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-7 items-end">
          {/* SEARCH */}
          <div className="space-y-1.5 col-span-1 sm:col-span-2">
            <Label className="flex items-center gap-1"><Search className="h-3 w-3" /> Search</Label>
            <Input
              placeholder="Search by name, email..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="rounded-xl border-slate-200 dark:border-slate-800"
            />
          </div>

          {/* ORG FILTER */}
          <div className="space-y-1.5">
            <Label className="flex items-center gap-1"><Filter className="h-3 w-3" /> Organization</Label>
            <select
              value={filterOrg}
              onChange={(e) => { setFilterOrg(e.target.value); setPage(1); }}
              className="w-full h-10 px-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
              disabled={user?.role !== 'SystemAdmin'}
            >
              <option value="">All</option>
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>{o.name}</option>
              ))}
            </select>
          </div>

          {/* DEPT FILTER */}
          <div className="space-y-1.5">
            <Label className="flex items-center gap-1"><Filter className="h-3 w-3" /> Department</Label>
            <select
              value={filterDept}
              onChange={(e) => { setFilterDept(e.target.value); setPage(1); }}
              className="w-full h-10 px-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              <option value="">All</option>
              {depts.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>

          {/* TEAM FILTER */}
          <div className="space-y-1.5">
            <Label className="flex items-center gap-1"><Filter className="h-3 w-3" /> Team</Label>
            <select
              value={filterTeam}
              onChange={(e) => { setFilterTeam(e.target.value); setPage(1); }}
              className="w-full h-10 px-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              <option value="">All</option>
              {teams.map((t) => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
          </div>

          {/* ROLE FILTER */}
          <div className="space-y-1.5">
            <Label className="flex items-center gap-1"><Filter className="h-3 w-3" /> Role</Label>
            <select
              value={filterRole}
              onChange={(e) => { setFilterRole(e.target.value); setPage(1); }}
              className="w-full h-10 px-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              <option value="">All Roles</option>
              <option value="SystemAdmin">Super Admin</option>
              <option value="OrgAdmin">Org Admin</option>
              <option value="Coordinator">Coordinator</option>
              <option value="Faculty">Faculty</option>
              <option value="Student">Student</option>
              <option value="Auditor">Auditor</option>
            </select>
          </div>

          {/* STATUS FILTER */}
          <div className="space-y-1.5">
            <Label className="flex items-center gap-1"><Filter className="h-3 w-3" /> Status</Label>
            <select
              value={filterStatus}
              onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}
              className="w-full h-10 px-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
            >
              <option value="">All Status</option>
              <option value="Active">Active</option>
              <option value="Inactive">Inactive</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* CORE LISTING */}
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
      ) : members.length === 0 ? (
        <Card className="border-2 border-dashed border-slate-200 dark:border-slate-800">
          <CardContent className="text-center py-16">
            <Users className="h-12 w-12 text-slate-350 dark:text-slate-650 mx-auto mb-4" />
            <p className="text-slate-600 dark:text-slate-400 font-semibold">No registered members found.</p>
            <p className="text-xs text-slate-400 mt-1">Directory registry is empty for selected filter configurations.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {members.map((m) => (
              <Card key={m.id} className={`overflow-hidden hover:shadow-lg transition-all duration-300 border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 ${!m.is_active ? 'opacity-65' : ''}`}>
                <CardHeader className="bg-slate-50/40 dark:bg-slate-950/10 pb-4 border-b border-slate-100 dark:border-slate-800/40">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary font-bold text-sm">
                        {m.full_name.charAt(0)}
                      </div>
                      <div>
                        <CardTitle className="text-sm font-bold text-slate-900 dark:text-white truncate max-w-[150px]">{m.full_name}</CardTitle>
                        <CardDescription className="text-[10px] uppercase font-bold tracking-wider text-slate-400">{m.role}</CardDescription>
                      </div>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${m.is_active ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300' : 'bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300'}`}>
                      {m.status}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-4 space-y-3.5 text-xs text-slate-650 dark:text-slate-400">
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-1.5 text-[11px] truncate">
                      <Mail className="h-3 w-3 text-slate-400 shrink-0" />
                      <span className="truncate">{m.email}</span>
                    </div>
                    {m.phone && (
                      <div className="flex items-center gap-1.5 text-[11px]">
                        <Phone className="h-3 w-3 text-slate-400 shrink-0" />
                        <span>{m.phone}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-1.5 text-[11px] text-slate-400 font-medium">
                      <Shield className="h-3 w-3 text-indigo-500 shrink-0" />
                      <span className="truncate">{m.organization?.name || 'No Organization'}</span>
                    </div>
                  </div>

                  {isSystemOrOrgAdmin && (
                    <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800/40">
                      <Button onClick={() => openEditModal(m)} size="sm" variant="outline" className="h-8 gap-1 rounded-lg">
                        <Edit2 className="h-3.5 w-3.5" />
                        Edit
                      </Button>
                      <Button
                        onClick={() => handleActivationToggle(m)}
                        size="sm"
                        variant={m.is_active ? 'destructive' : 'outline'}
                        className="h-8 gap-1 rounded-lg"
                      >
                        {m.is_active ? (
                          <>
                            <UserMinus className="h-3.5 w-3.5" />
                            Deactivate
                          </>
                        ) : (
                          <>
                            <UserCheck className="h-3.5 w-3.5" />
                            Activate
                          </>
                        )}
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
      )}

      {/* MEMBER MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900 animate-in zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
              {editingMember ? 'Edit Member Profile' : 'Register Member'}
            </h3>
            <p className="text-xs text-slate-500 mb-6">
              Establish and binds profile information.
            </p>

            <form onSubmit={handleFormSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="memName">Full Name *</Label>
                  <Input
                    id="memName"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. John Doe"
                    required
                    disabled={submitting}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="memEmail">Email Address *</Label>
                  <Input
                    id="memEmail"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="john@example.com"
                    required
                    disabled={submitting}
                  />
                </div>
              </div>

              {!editingMember && (
                <div className="space-y-1.5">
                  <Label htmlFor="memPwd">Password *</Label>
                  <Input
                    id="memPwd"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    disabled={submitting}
                  />
                </div>
              )}

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="memRole">System Role *</Label>
                  <select
                    id="memRole"
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="w-full h-10 px-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                    required
                    disabled={submitting}
                  >
                    <option value="Student">Student</option>
                    <option value="Faculty">Faculty</option>
                    <option value="Coordinator">Coordinator</option>
                    <option value="OrgAdmin">Org Admin</option>
                    <option value="SystemAdmin">Super Admin</option>
                    <option value="Auditor">Auditor</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="memPhone">Phone Number</Label>
                  <Input
                    id="memPhone"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+1-555-0123"
                    disabled={submitting}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="memGender">Gender</Label>
                  <select
                    id="memGender"
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className="w-full h-10 px-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                    disabled={submitting}
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="memOrg">Organization Bind *</Label>
                <select
                  id="memOrg"
                  value={orgId}
                  onChange={(e) => setOrgId(Number(e.target.value) || '')}
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
                  <Label htmlFor="memDept">Department</Label>
                  <select
                    id="memDept"
                    value={deptId}
                    onChange={(e) => setDeptId(Number(e.target.value) || '')}
                    className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                    disabled={submitting}
                  >
                    <option value="">Select Department...</option>
                    {depts.map((d) => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="memTeam">Team</Label>
                  <select
                    id="memTeam"
                    value={teamId}
                    onChange={(e) => setTeamId(Number(e.target.value) || '')}
                    className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm"
                    disabled={submitting}
                  >
                    <option value="">Select Team...</option>
                    {teams.map((t) => (
                      <option key={t.id} value={t.id}>{t.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="memEmergency">Emergency Contact</Label>
                  <Input
                    id="memEmergency"
                    value={emergencyContact}
                    onChange={(e) => setEmergencyContact(e.target.value)}
                    placeholder="Contact Name (+1...)"
                    disabled={submitting}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="memJoinDate">Joining Date</Label>
                  <Input
                    id="memJoinDate"
                    type="date"
                    value={joiningDate}
                    onChange={(e) => setJoiningDate(e.target.value)}
                    disabled={submitting}
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)} disabled={submitting} className="rounded-lg">
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting} className="rounded-lg gap-2">
                  {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                  {editingMember ? 'Save Changes' : 'Create'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
