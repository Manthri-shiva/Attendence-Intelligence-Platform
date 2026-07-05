import React, { useState, useEffect } from 'react';
import api from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Building2, Plus, Edit2, Trash2, Search, Loader2, Globe, Clock, ShieldAlert } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToastStore } from '@/store/toastStore';
import { useAuthStore } from '@/store/authStore';

interface Organization {
  id: number;
  name: string;
  logo?: string;
  description?: string;
  email?: string;
  phone?: string;
  website?: string;
  country?: string;
  state?: string;
  city?: string;
  timezone: string;
  address?: string;
  status: string;
  created_at: string;
}

export default function OrganizationsPage() {
  const { user } = useAuthStore();
  const { addToast } = useToastStore();
  
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Search and Pagination states
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const limit = 5;

  // Modal forms states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingOrg, setEditingOrg] = useState<Organization | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form Fields
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [website, setWebsite] = useState('');
  const [timezone, setTimezone] = useState('UTC');
  const [status, setStatus] = useState('Active');

  const fetchOrganizations = async () => {
    setLoading(true);
    setError(null);
    try {
      const skip = (page - 1) * limit;
      const response = await api.get(`/organizations/?skip=${skip}&limit=${limit}&q=${search}`);
      if (response.data && response.data.success) {
        setOrgs(response.data.data || []);
        // Extract total count message or just set totalCount based on length/estimate
        const msg = response.data.message || '';
        const match = msg.match(/Total: (\d+)/);
        setTotalCount(match ? parseInt(match[1]) : (response.data.data?.length || 0));
      } else {
        setError('Failed to load organizations.');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'An error occurred while loading organizations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrganizations();
  }, [search, page]);

  const openCreateModal = () => {
    setEditingOrg(null);
    setName('');
    setDescription('');
    setEmail('');
    setPhone('');
    setWebsite('');
    setTimezone('UTC');
    setStatus('Active');
    setIsModalOpen(true);
  };

  const openEditModal = (org: Organization) => {
    setEditingOrg(org);
    setName(org.name);
    setDescription(org.description || '');
    setEmail(org.email || '');
    setPhone(org.phone || '');
    setWebsite(org.website || '');
    setTimezone(org.timezone || 'UTC');
    setStatus(org.status || 'Active');
    setIsModalOpen(true);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      addToast('Organization name is required.', 'error');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        name,
        description: description || null,
        email: email || null,
        phone: phone || null,
        website: website || null,
        timezone,
        status
      };

      if (editingOrg) {
        await api.put(`/organizations/${editingOrg.id}`, payload);
        addToast('Organization updated successfully.', 'success');
      } else {
        await api.post('/organizations/', payload);
        addToast('Organization created successfully.', 'success');
      }
      setIsModalOpen(false);
      fetchOrganizations();
    } catch (err: any) {
      const errMsg = err.response?.data?.errors?.[0]?.detail || err.response?.data?.message || 'Request failed.';
      addToast(errMsg, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to deactivate this organization? This will mark its status as Inactive.')) {
      return;
    }
    try {
      await api.delete(`/organizations/${id}`);
      addToast('Organization deactivated successfully.', 'success');
      fetchOrganizations();
    } catch (err: any) {
      addToast(err.response?.data?.message || 'Deactivation failed.', 'error');
    }
  };

  const isSystemAdmin = user?.role === 'SystemAdmin';
  const totalPages = Math.ceil(totalCount / limit);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Organizations
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Configure and manage global enterprise organization boundaries.
          </p>
        </div>
        {isSystemAdmin && (
          <Button onClick={openCreateModal} className="gap-2 rounded-xl">
            <Plus className="h-4 w-4" />
            Add Organization
          </Button>
        )}
      </div>

      {/* SEARCH BAR */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <Input
          placeholder="Search organizations..."
          className="pl-9 rounded-xl border-slate-200 dark:border-slate-800"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
      </div>

      {/* CORE CONTENT LAYOUT */}
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
      ) : orgs.length === 0 ? (
        <Card className="border-2 border-dashed border-slate-200 dark:border-slate-800">
          <CardContent className="text-center py-16">
            <Building2 className="h-12 w-12 text-slate-350 dark:text-slate-600 mx-auto mb-4" />
            <p className="text-slate-650 dark:text-slate-400 font-semibold">No organizations found.</p>
            <p className="text-xs text-slate-400 mt-1">Try matching another keyword or register a new organization node.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {orgs.map((org) => (
              <Card key={org.id} className="overflow-hidden hover:shadow-lg transition-all duration-300 border-slate-250/70 bg-white dark:border-slate-800 dark:bg-slate-900">
                <CardHeader className="bg-slate-50/50 dark:bg-slate-950/20 pb-4 border-b border-slate-100 dark:border-slate-800/60">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
                        <Building2 className="h-5 w-5" />
                      </div>
                      <div>
                        <CardTitle className="text-lg font-bold text-slate-900 dark:text-white">{org.name}</CardTitle>
                        <CardDescription className="text-xs">{org.city || 'Global scope'}, {org.country || 'AIP System'}</CardDescription>
                      </div>
                    </div>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${org.status === 'Active' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'}`}>
                      {org.status}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="p-5 space-y-4 text-sm text-slate-600 dark:text-slate-400">
                  <p className="text-xs text-slate-500 line-clamp-2">{org.description || 'No description provided.'}</p>
                  
                  <div className="space-y-1.5 pt-2 border-t border-slate-100 dark:border-slate-800/40">
                    <div className="flex items-center gap-2 text-xs">
                      <Globe className="h-3.5 w-3.5 text-slate-400" />
                      <span className="truncate">{org.website || org.email || 'No contact details'}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <Clock className="h-3.5 w-3.5 text-slate-400" />
                      <span>Timezone: <b>{org.timezone}</b></span>
                    </div>
                  </div>

                  {isSystemAdmin && (
                    <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800/40">
                      <Button onClick={() => openEditModal(org)} size="sm" variant="outline" className="gap-1 rounded-lg">
                        <Edit2 className="h-3.5 w-3.5" />
                        Edit
                      </Button>
                      <Button onClick={() => handleDelete(org.id)} size="sm" variant="destructive" className="gap-1 rounded-lg" disabled={org.status === 'Inactive'}>
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
      )}

      {/* CREATE / EDIT MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900 animate-in zoom-in-95 duration-200">
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
              {editingOrg ? 'Edit Organization' : 'Create Organization'}
            </h3>
            <p className="text-xs text-slate-500 mb-6">
              Configure parameters for this tenant boundary node.
            </p>

            <form onSubmit={handleFormSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="orgName">Organization Name *</Label>
                <Input
                  id="orgName"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Acme Corporation"
                  required
                  disabled={submitting}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="orgDesc">Description</Label>
                <Input
                  id="orgDesc"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Brief description about the entity"
                  disabled={submitting}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="orgEmail">Email Address</Label>
                  <Input
                    id="orgEmail"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="ops@acme.com"
                    disabled={submitting}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="orgPhone">Phone Number</Label>
                  <Input
                    id="orgPhone"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+1 (555) 012-3456"
                    disabled={submitting}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label htmlFor="orgTz">Timezone</Label>
                  <select
                    id="orgTz"
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                    className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                    disabled={submitting}
                  >
                    <option value="UTC">UTC (Coordinated Universal Time)</option>
                    <option value="America/New_York">EST (Eastern Standard Time)</option>
                    <option value="America/Chicago">CST (Central Standard Time)</option>
                    <option value="America/Denver">MST (Mountain Standard Time)</option>
                    <option value="America/Los_Angeles">PST (Pacific Standard Time)</option>
                    <option value="Europe/London">GMT (London Time)</option>
                    <option value="Asia/Kolkata">IST (Indian Standard Time)</option>
                    <option value="Asia/Tokyo">JST (Japan Standard Time)</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="orgStatus">Status</Label>
                  <select
                    id="orgStatus"
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                    className="w-full h-10 px-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                    disabled={submitting}
                  >
                    <option value="Active">Active</option>
                    <option value="Inactive">Inactive</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
                <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)} disabled={submitting} className="rounded-lg">
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting} className="rounded-lg gap-2">
                  {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
                  {editingOrg ? 'Save Changes' : 'Create'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
