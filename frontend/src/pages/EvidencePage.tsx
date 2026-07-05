import React, { useState, useEffect } from 'react';
import api from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { useToastStore } from '@/store/toastStore';
import { useAuthStore } from '@/store/authStore';
import {
  Eye,
  Search,
  Filter,
  ShieldAlert,
  MapPin,
  Smartphone,
  Chrome,
  Network,
  Calendar,
  Clock,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  X,
  Download,
  Loader2,
  ExternalLink
} from 'lucide-react';

interface AttendanceRecord {
  id: number;
  member_id: number;
  session_id: number;
  status: string;
  gps_status: string;
  verification_status: string;
  check_in_time: string;
  confidence_score: number | null;
  liveness_score: number | null;
  selfie_image_path: string | null;
  member?: {
    full_name: string;
    email: string;
    profile_photo: string | null;
  };
  session?: {
    name: string;
    date: string;
  };
}

interface EvidenceDetail {
  attendance_id: number;
  member_id: number;
  member_name: string;
  profile_photo: string | null;
  selfie_image_path: string | null;
  session_name: string;
  check_in_time: string | null;
  gps_latitude: number | null;
  gps_longitude: number | null;
  gps_accuracy: number | null;
  verification_status: string | null;
  confidence_score: number | null;
  liveness_score: number | null;
  device_name: string | null;
  browser_name: string | null;
  user_agent: string | null;
  ip_address: string | null;
  captured_at: string | null;
}

export default function EvidencePage() {
  const { user } = useAuthStore();
  const { addToast } = useToastStore();

  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<any>({
    today_attendance: 0,
    verified_attendance: 0,
    pending_verification: 0,
    rejected_attendance: 0
  });

  // Filter lists
  const [orgs, setOrgs] = useState<any[]>([]);
  const [depts, setDepts] = useState<any[]>([]);
  const [teams, setTeams] = useState<any[]>([]);
  const [members, setMembers] = useState<any[]>([]);

  // Filter form states
  const [searchQuery, setSearchQuery] = useState('');
  const [filterOrg, setFilterOrg] = useState('');
  const [filterDept, setFilterDept] = useState('');
  const [filterTeam, setFilterTeam] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterDate, setFilterDate] = useState('');

  // Modal State
  const [selectedRecordId, setSelectedRecordId] = useState<number | null>(null);
  const [evidenceDetail, setEvidenceDetail] = useState<EvidenceDetail | null>(null);
  const [loadingEvidence, setLoadingEvidence] = useState(false);
  const [enlargeImage, setEnlargeImage] = useState(false);

  const loadHelpers = async () => {
    try {
      const orgsRes = await api.get('/organizations/?limit=100');
      if (orgsRes.data?.success) setOrgs(orgsRes.data.data || []);

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

  const fetchDashboardStats = async () => {
    try {
      const statsRes = await api.get('/analytics/dashboard');
      if (statsRes.data?.success) {
        setStats(statsRes.data.data);
      }
    } catch {
      // Fail silently
    }
  };

  const fetchRecords = async () => {
    setLoading(true);
    try {
      let queryStr = `/sessions/attendances/all?limit=100`;
      if (searchQuery) queryStr += `&q=${searchQuery}`;
      if (filterOrg) queryStr += `&organization_id=${filterOrg}`;
      if (filterDept) queryStr += `&department_id=${filterDept}`;
      if (filterTeam) queryStr += `&team_id=${filterTeam}`;
      if (filterStatus) queryStr += `&status=${filterStatus}`;
      if (filterDate) queryStr += `&date=${filterDate}`;

      const res = await api.get(queryStr);
      if (res.data?.success) {
        setRecords(res.data.data || []);
      }
    } catch (err: any) {
      addToast(err.response?.data?.message || 'Failed to fetch attendance logs.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHelpers();
    fetchDashboardStats();
  }, []);

  useEffect(() => {
    fetchRecords();
  }, [searchQuery, filterOrg, filterDept, filterTeam, filterStatus, filterDate]);

  const handleOpenEvidence = async (id: number) => {
    setSelectedRecordId(id);
    setLoadingEvidence(true);
    setEvidenceDetail(null);
    setEnlargeImage(false);
    try {
      const res = await api.get(`/sessions/attendances/${id}/evidence`);
      if (res.data?.success) {
        setEvidenceDetail(res.data.data);
      }
    } catch (err: any) {
      addToast(err.response?.data?.message || 'Access denied to biometric evidence logs.', 'error');
      setSelectedRecordId(null);
    } finally {
      setLoadingEvidence(false);
    }
  };

  const handleCloseEvidence = () => {
    setSelectedRecordId(null);
    setEvidenceDetail(null);
    setEnlargeImage(false);
  };

  // Enforce role-based selfie downloading
  const canDownload = user?.role === 'SystemAdmin' || user?.role === 'OrgAdmin';

  const handleDownloadSelfie = () => {
    if (!canDownload || !evidenceDetail?.selfie_image_path) return;
    
    // Resolve full server URL
    const baseUrl = api.defaults.baseURL?.replace('/api/v1', '') || 'http://localhost:8000';
    const imageUrl = `${baseUrl}/${evidenceDetail.selfie_image_path}`;
    
    const link = document.createElement('a');
    link.href = imageUrl;
    link.target = '_blank';
    link.setAttribute('download', `selfie_${evidenceDetail.member_name.replace(/\s+/g, '_')}.jpg`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    
    addToast('Selfie download initiated.', 'success');
  };

  const resolveImageUrl = (path: string | null) => {
    if (!path) return null;
    const baseUrl = api.defaults.baseURL?.replace('/api/v1', '') || 'http://localhost:8000';
    return `${baseUrl}/${path}`;
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Biometric Attendance Evidence
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Browse and audit selfie frames, geofence variables, and AI confirmation metrics.
          </p>
        </div>
      </div>

      {/* STATISTICS ROW */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 rounded-2xl shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Today's Attendance
            </CardTitle>
            <Calendar className="h-4 w-4 text-indigo-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-black text-slate-900 dark:text-white">
              {stats.today_attendance || 0}
            </div>
            <p className="text-xxs text-slate-400 mt-1">Checked in today</p>
          </CardContent>
        </Card>

        <Card className="border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 rounded-2xl shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Verified Attendance
            </CardTitle>
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-black text-slate-900 dark:text-white">
              {stats.verified_attendance || 0}
            </div>
            <p className="text-xxs text-slate-400 mt-1">AI Match Successes</p>
          </CardContent>
        </Card>

        <Card className="border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 rounded-2xl shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Pending Verification
            </CardTitle>
            <Clock className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-black text-slate-900 dark:text-white">
              {stats.pending_verification || 0}
            </div>
            <p className="text-xxs text-slate-400 mt-1">Awaiting fallback review</p>
          </CardContent>
        </Card>

        <Card className="border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 rounded-2xl shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Rejected Attendance
            </CardTitle>
            <AlertCircle className="h-4 w-4 text-rose-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-black text-slate-900 dark:text-white">
              {stats.rejected_attendance || 0}
            </div>
            <p className="text-xxs text-slate-400 mt-1">Liveness / Confidence failed</p>
          </CardContent>
        </Card>
      </div>

      {/* FILTER PANEL */}
      <Card className="border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 rounded-2xl shadow-sm">
        <CardContent className="p-6 space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search Name, Email, Session..."
                className="pl-9 bg-slate-50 border-slate-200 dark:bg-slate-950 dark:border-slate-800 rounded-xl text-sm"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <select
                className="w-full text-xs bg-slate-50 border border-slate-200 dark:bg-slate-950 dark:border-slate-800 rounded-xl px-3 py-2 text-slate-700 dark:text-slate-350 focus:outline-none"
                value={filterOrg}
                onChange={(e) => setFilterOrg(e.target.value)}
              >
                <option value="">All Orgs</option>
                {orgs.map((o) => (
                  <option key={o.id} value={o.id}>{o.name}</option>
                ))}
              </select>

              <select
                className="w-full text-xs bg-slate-50 border border-slate-200 dark:bg-slate-950 dark:border-slate-800 rounded-xl px-3 py-2 text-slate-700 dark:text-slate-350 focus:outline-none"
                value={filterDept}
                onChange={(e) => setFilterDept(e.target.value)}
              >
                <option value="">All Depts</option>
                {depts.map((d) => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <select
                className="w-full text-xs bg-slate-50 border border-slate-200 dark:bg-slate-950 dark:border-slate-800 rounded-xl px-2 py-2 text-slate-700 dark:text-slate-350 focus:outline-none"
                value={filterTeam}
                onChange={(e) => setFilterTeam(e.target.value)}
              >
                <option value="">All Teams</option>
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </select>

              <select
                className="w-full text-xs bg-slate-50 border border-slate-200 dark:bg-slate-950 dark:border-slate-800 rounded-xl px-2 py-2 text-slate-700 dark:text-slate-350 focus:outline-none"
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
              >
                <option value="">All Statuses</option>
                <option value="Present">Present</option>
                <option value="Late">Late</option>
                <option value="Absent">Absent</option>
                <option value="Excused">Excused</option>
                <option value="Pending Approval">Pending Approval</option>
              </select>

              <Input
                type="date"
                className="text-xs bg-slate-50 border-slate-200 dark:bg-slate-950 dark:border-slate-800 rounded-xl h-8 py-0 px-2"
                value={filterDate}
                onChange={(e) => setFilterDate(e.target.value)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* TABLE PANEL */}
      <Card className="border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 rounded-2xl overflow-hidden shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/20 text-slate-500 font-semibold h-10">
                  <th className="px-6">Member</th>
                  <th className="px-6">Session</th>
                  <th className="px-6">Check-in Time</th>
                  <th className="px-6">Attendance Status</th>
                  <th className="px-6">Verification</th>
                  <th className="px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-850">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="text-center py-12">
                      <div className="flex flex-col items-center gap-2">
                        <Loader2 className="h-6 w-6 animate-spin text-indigo-500" />
                        <p className="text-slate-500">Loading evidence logs...</p>
                      </div>
                    </td>
                  </tr>
                ) : records.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-12 text-slate-400">
                      No matching attendance records found.
                    </td>
                  </tr>
                ) : (
                  records.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50/30 dark:hover:bg-slate-950/5 h-12">
                      <td className="px-6 py-2">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full overflow-hidden bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex-shrink-0 flex items-center justify-center font-bold text-slate-400">
                            {r.member?.profile_photo ? (
                              <img
                                src={resolveImageUrl(r.member.profile_photo) || undefined}
                                className="w-full h-full object-cover"
                                alt=""
                              />
                            ) : (
                              r.member?.full_name.charAt(0)
                            )}
                          </div>
                          <div>
                            <p className="font-semibold text-slate-800 dark:text-slate-250">
                              {r.member?.full_name}
                            </p>
                            <p className="text-slate-400 text-xxs">
                              {r.member?.email}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6">
                        <span className="font-medium text-slate-700 dark:text-slate-350">
                          {r.session?.name}
                        </span>
                      </td>
                      <td className="px-6 text-slate-500">
                        {r.check_in_time ? new Date(r.check_in_time).toLocaleString() : 'N/A'}
                      </td>
                      <td className="px-6">
                        <span className={`px-2 py-0.5 rounded-full text-xxs font-bold inline-block border ${
                          r.status === 'Present'
                            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-500'
                            : r.status === 'Late'
                            ? 'bg-amber-500/10 border-amber-500/20 text-amber-500'
                            : r.status === 'Pending Approval'
                            ? 'bg-sky-500/10 border-sky-500/20 text-sky-500'
                            : 'bg-rose-500/10 border-rose-500/20 text-rose-500'
                        }`}>
                          {r.status}
                        </span>
                      </td>
                      <td className="px-6">
                        <span className={`px-2 py-0.5 rounded-full text-xxs font-bold inline-block border ${
                          r.verification_status === 'Verified'
                            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-500'
                            : r.verification_status === 'Pending'
                            ? 'bg-amber-500/10 border-amber-500/20 text-amber-500'
                            : 'bg-rose-500/10 border-rose-500/20 text-rose-500'
                        }`}>
                          {r.verification_status}
                        </span>
                      </td>
                      <td className="px-6 text-right">
                        <Button
                          variant="secondary"
                          size="sm"
                          className="rounded-xl gap-1.5 h-8 text-xxs px-2.5"
                          onClick={() => handleOpenEvidence(r.id)}
                          disabled={!r.selfie_image_path}
                        >
                          <Eye className="h-3 w-3" />
                          View Evidence
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* EVIDENCE DETAIL MODAL */}
      {selectedRecordId !== null && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="max-w-2xl w-full border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 rounded-3xl overflow-hidden shadow-2xl relative max-h-[90vh] flex flex-col">
            <button
              onClick={handleCloseEvidence}
              className="absolute right-4 top-4 text-slate-400 hover:text-slate-600 dark:hover:text-white z-10"
            >
              <X className="h-5 w-5" />
            </button>

            {loadingEvidence ? (
              <div className="flex h-80 items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
              </div>
            ) : !evidenceDetail ? (
              <div className="p-8 text-center text-slate-500">
                Failed to fetch evidence metadata.
              </div>
            ) : (
              <>
                <CardHeader className="border-b border-slate-100 dark:border-slate-850 p-6 flex flex-row items-center gap-4">
                  <div className="w-12 h-12 rounded-full overflow-hidden bg-slate-100 dark:bg-slate-850 border border-slate-200 dark:border-slate-800 flex items-center justify-center font-bold text-slate-400 flex-shrink-0">
                    {evidenceDetail.profile_photo ? (
                      <img src={resolveImageUrl(evidenceDetail.profile_photo) || undefined} className="w-full h-full object-cover" alt="" />
                    ) : (
                      evidenceDetail.member_name.charAt(0)
                    )}
                  </div>
                  <div>
                    <CardTitle className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                      {evidenceDetail.member_name}
                      <span className={`px-2 py-0.5 rounded-full text-xxs font-black border ${
                        evidenceDetail.verification_status === 'Verified'
                          ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-500'
                          : 'bg-rose-500/10 border-rose-500/20 text-rose-500'
                      }`}>
                        {evidenceDetail.verification_status}
                      </span>
                    </CardTitle>
                    <CardDescription className="text-xxs">
                      Session: <b className="text-slate-800 dark:text-slate-300">{evidenceDetail.session_name}</b>
                    </CardDescription>
                  </div>
                </CardHeader>

                <div className="overflow-y-auto p-6 space-y-6 flex-1">
                  {/* TWO COLUMN SUMMARY */}
                  <div className="grid md:grid-cols-2 gap-6">
                    {/* LEFT COLUMN: SELFIE FRAME */}
                    <div className="space-y-2">
                      <Label className="text-xxs uppercase tracking-wider text-slate-400 font-bold">Attendance Selfie</Label>
                      {evidenceDetail.selfie_image_path ? (
                        <div className="relative group rounded-2xl overflow-hidden bg-black aspect-square border border-slate-200 dark:border-slate-800 flex items-center justify-center">
                          <img
                            src={resolveImageUrl(evidenceDetail.selfie_image_path) || undefined}
                            className={`w-full h-full object-cover cursor-zoom-in transition-transform duration-300 ${enlargeImage ? 'scale-125' : ''}`}
                            onClick={() => setEnlargeImage(!enlargeImage)}
                            alt="Attendance Selfie"
                          />
                          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center pointer-events-none">
                            <span className="text-white text-xxs font-medium bg-black/60 px-3 py-1.5 rounded-full flex items-center gap-1">
                              <Eye className="h-3 w-3" /> Click to {enlargeImage ? 'Shrink' : 'Enlarge'}
                            </span>
                          </div>
                          
                          {/* Download restricted to Admins */}
                          {canDownload && (
                            <Button
                              onClick={handleDownloadSelfie}
                              className="absolute bottom-2 right-2 rounded-xl bg-slate-900/80 hover:bg-slate-950 text-white p-2 h-8 w-8"
                              title="Download original frame"
                            >
                              <Download className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      ) : (
                        <div className="h-40 rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex items-center justify-center text-slate-400 text-xs">
                          No selfie image stored.
                        </div>
                      )}
                    </div>

                    {/* RIGHT COLUMN: GPS & AUDIT LOG */}
                    <div className="space-y-4">
                      {/* GPS Details */}
                      <div className="bg-slate-50 dark:bg-slate-950 p-4 rounded-2xl space-y-3 border border-slate-100 dark:border-slate-850">
                        <Label className="text-xxs uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1.5">
                          <MapPin className="h-3.5 w-3.5 text-red-500" /> Captured GPS Position
                        </Label>
                        
                        {/* Map coordinates details */}
                        <div className="space-y-1.5 text-xs text-slate-600 dark:text-slate-350 font-medium">
                          <div className="flex justify-between">
                            <span>Latitude:</span>
                            <span className="font-bold text-slate-900 dark:text-white">{evidenceDetail.gps_latitude || 'N/A'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Longitude:</span>
                            <span className="font-bold text-slate-900 dark:text-white">{evidenceDetail.gps_longitude || 'N/A'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Accuracy:</span>
                            <span className="font-bold text-slate-900 dark:text-white">
                              {evidenceDetail.gps_accuracy ? `${evidenceDetail.gps_accuracy.toFixed(1)} meters` : 'N/A'}
                            </span>
                          </div>
                          
                          {evidenceDetail.gps_latitude && evidenceDetail.gps_longitude && (
                            <a
                              href={`https://www.google.com/maps?q=${evidenceDetail.gps_latitude},${evidenceDetail.gps_longitude}`}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1 text-primary hover:underline text-xxs mt-2 font-semibold"
                            >
                              <ExternalLink className="h-3 w-3" /> View on Google Maps
                            </a>
                          )}
                        </div>
                      </div>

                      {/* Device & Client Metadata */}
                      <div className="bg-slate-50 dark:bg-slate-950 p-4 rounded-2xl space-y-3 border border-slate-100 dark:border-slate-850">
                        <Label className="text-xxs uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1.5">
                          <Smartphone className="h-3.5 w-3.5 text-indigo-500" /> Device & Browser info
                        </Label>
                        <div className="space-y-1.5 text-xs text-slate-600 dark:text-slate-350 font-medium">
                          <div className="flex justify-between">
                            <span className="flex items-center gap-1"><Smartphone className="h-3 w-3 text-slate-400" /> OS/Device:</span>
                            <span className="font-bold text-slate-900 dark:text-white">{evidenceDetail.device_name || 'Unknown'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="flex items-center gap-1"><Chrome className="h-3 w-3 text-slate-400" /> Browser:</span>
                            <span className="font-bold text-slate-900 dark:text-white">{evidenceDetail.browser_name || 'Unknown'}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="flex items-center gap-1"><Network className="h-3 w-3 text-slate-400" /> IP Address:</span>
                            <span className="font-bold text-slate-900 dark:text-white">{evidenceDetail.ip_address || 'N/A'}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* AI PIPELINE METADATA */}
                  <div className="grid md:grid-cols-3 gap-3">
                    <div className="bg-slate-50 dark:bg-slate-950 p-3 rounded-xl border border-slate-100 dark:border-slate-850 text-center">
                      <p className="text-slate-400 text-xxs uppercase font-semibold">AI Similarity Match</p>
                      <p className="text-lg font-black text-slate-900 dark:text-white mt-1">
                        {evidenceDetail.confidence_score ? `${(evidenceDetail.confidence_score * 100).toFixed(0)}%` : 'N/A'}
                      </p>
                    </div>

                    <div className="bg-slate-50 dark:bg-slate-950 p-3 rounded-xl border border-slate-100 dark:border-slate-850 text-center">
                      <p className="text-slate-400 text-xxs uppercase font-semibold">Liveness Score</p>
                      <p className="text-lg font-black text-slate-900 dark:text-white mt-1">
                        {evidenceDetail.liveness_score ? `${(evidenceDetail.liveness_score * 100).toFixed(0)}%` : 'N/A'}
                      </p>
                    </div>

                    <div className="bg-slate-50 dark:bg-slate-950 p-3 rounded-xl border border-slate-100 dark:border-slate-850 text-center">
                      <p className="text-slate-400 text-xxs uppercase font-semibold">Check-in Time</p>
                      <p className="text-xs font-bold text-slate-900 dark:text-white mt-1 flex items-center justify-center gap-1.5 h-6">
                        <Clock className="h-3.5 w-3.5 text-indigo-500" />
                        {evidenceDetail.check_in_time ? new Date(evidenceDetail.check_in_time).toLocaleTimeString() : 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="border-t border-slate-100 dark:border-slate-850 p-6 flex justify-end">
                  <Button onClick={handleCloseEvidence} variant="outline" className="rounded-xl">
                    Close Details
                  </Button>
                </div>
              </>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
