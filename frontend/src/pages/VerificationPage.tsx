import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import api from '@/services/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useToastStore } from '@/store/toastStore';
import {
  Camera, Loader2, ShieldCheck, ShieldAlert, RefreshCw, CheckCircle2,
  MapPin, UserCheck, Eye, EyeOff, Sliders, AlertTriangle
} from 'lucide-react';

interface SessionDetail {
  id: number;
  name: string;
  session_type: string;
  gps_radius?: number;
  face_confidence_threshold?: number;
  fallback_policy?: string;
  latitude?: number;
  longitude?: number;
}

export default function VerificationPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { addToast } = useToastStore();

  const sessionIdParam = searchParams.get('session_id');
  const sessionId = sessionIdParam ? parseInt(sessionIdParam) : null;

  const [session, setSession] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [cameraActive, setCameraActive] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successData, setSuccessData] = useState<any | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [location, setLocation] = useState<{
    latitude: number;
    longitude: number;
    accuracy: number;
  } | null>(null);
  const [gpsLoading, setGpsLoading] = useState(false);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Verification Pipeline Steps
  const [steps, setSteps] = useState([
    { name: '1. Session Bounds validation', status: 'idle' },
    { name: '2. GPS Geofence Check', status: 'idle' },
    { name: '3. Face Similarity matching', status: 'idle' },
    { name: '4. Liveness Spoof evaluation', status: 'idle' },
    { name: '5. Logging verified attendance', status: 'idle' }
  ]);

  // Test Simulator Configurations
  const [simConfidence, setSimConfidence] = useState(0.92);
  const [simLiveness, setSimLiveness] = useState('None');
  const [gpsSimValid, setGpsSimValid] = useState(true);

  // WebRTC Camera Video Ref
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const fetchSession = async () => {
    if (!sessionId) {
      setErrorMsg('No session ID specified in the verification link.');
      setLoading(false);
      return;
    }
    try {
      const res = await api.get(`/sessions/${sessionId}`);
      if (res.data?.success) {
        setSession(res.data.data);
      } else {
        setErrorMsg('Failed to locate session details.');
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.message || 'Error locating session.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSession();
    return () => {
      stopCamera();
    };
  }, [sessionId]);

  const startCamera = async () => {
    setErrorMsg(null);
    setSuccessData(null);
    setCameraActive(false);
    try {
      if (streamRef.current) {
        stopCamera();
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' },
        audio: false
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setCameraActive(true);
    } catch {
      addToast('Could not initialize camera feed. Please check permissions.', 'error');
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
  };

  // Trigger Camera automatically on session load
  useEffect(() => {
    if (session) {
      startCamera();
      captureLocation();
    }
  }, [session]);

  const captureSelfie = (): string | null => {
    if (!videoRef.current || !canvasRef.current) return null;

    const video = videoRef.current;
    const canvas = canvasRef.current;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    // Mirror image so it matches preview
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const image = canvas.toDataURL("image/jpeg", 0.9);

    setCapturedImage(image);

    return image;
  };

  const captureLocation = async (): Promise<boolean> => {
    if (!navigator.geolocation) {
      addToast("Geolocation is not supported by this browser.", "error");
      return false;
    }

    setGpsLoading(true);

    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLocation({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy
          });
          setGpsLoading(false);
          resolve(true);
        },
        () => {
          setGpsLoading(false);
          addToast("Unable to retrieve GPS location.", "error");
          resolve(false);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        }
      );
    });
  };

  const runVerification = async () => {
    if (!sessionId || verifying) return;
    setVerifying(true);
    setSuccessData(null);
    setErrorMsg(null);

    const image = captureSelfie();
    if (!image) {
      addToast("Unable to capture selfie.", "error");
      setVerifying(false);
      return;
    }

    const gpsCaptured = await captureLocation();
    if (!gpsCaptured) {
      setVerifying(false);
      return;
    }

    // Reset pipeline step UI states
    setSteps([
      { name: '1. Session Bounds validation', status: 'pending' },
      { name: '2. GPS Geofence Check', status: 'idle' },
      { name: '3. Face Similarity matching', status: 'idle' },
      { name: '4. Liveness Spoof evaluation', status: 'idle' },
      { name: '5. Logging verified attendance', status: 'idle' }
    ]);

    const updateStep = (index: number, status: 'idle' | 'pending' | 'success' | 'fail') => {
      setSteps((prev) => {
        const next = [...prev];
        next[index].status = status;
        if (status === 'success' && index + 1 < next.length) {
          next[index + 1].status = 'pending';
        }
        return next;
      });
    };

    try {
      // Step 1: Session Validation
      await new Promise((r) => setTimeout(r, 600));
      updateStep(0, 'success');

      // Step 2: GPS check
      await new Promise((r) => setTimeout(r, 800));
      // Determine coordinates
      const lat = location ? location.latitude : 12.9716;
      const lon = location ? location.longitude : 77.5946;

      if (!gpsSimValid) {
        updateStep(1, 'fail');
        throw new Error('Check-in rejected: Outside allowed GPS geofence area.');
      }
      updateStep(1, 'success');

      // Step 3: Face similarity
      await new Promise((r) => setTimeout(r, 1000));
      const threshold = session?.face_confidence_threshold || 0.85;
      if (simConfidence < threshold && (session?.fallback_policy || 'Block') === 'Block') {
        updateStep(2, 'fail');
        throw new Error(`AI Face matching failed. Match confidence ${(simConfidence * 100).toFixed(0)}% below required ${(threshold * 100).toFixed(0)}%.`);
      }
      updateStep(2, 'success');

      // Step 4: Liveness Spoof Check
      await new Promise((r) => setTimeout(r, 800));
      if (simLiveness !== 'None') {
        updateStep(3, 'fail');
        throw new Error(`Anti-Spoof check failed: ${simLiveness} spoof attempt detected.`);
      }
      updateStep(3, 'success');

      // Step 5: Backend persistence log
      const payload = {
        session_id: sessionId,
        latitude: lat,
        longitude: lon,
        accuracy: location ? location.accuracy : null,
        captured_at: new Date().toISOString(),
        image_b64: image || 'test_biometric_base64_captured_frame',
        simulate_confidence: simConfidence,
        simulate_liveness: simLiveness === 'None' ? null : simLiveness
      };

      const res = await api.post(`/sessions/${sessionId}/check-in`, payload);
      await new Promise((r) => setTimeout(r, 500));

      if (res.data?.success) {
        updateStep(4, 'success');
        setSuccessData(res.data.data);
        addToast('Biometric attendance check-in completed.', 'success');
        stopCamera();
      } else {
        updateStep(4, 'fail');
        throw new Error('Biometric database registration failed.');
      }

    } catch (err: any) {
      const msg = err.response?.data?.message || err.message || 'Verification pipeline rejected.';
      setErrorMsg(msg);
      addToast(msg, 'error');
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-500">
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          Biometric AI Verification
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Complete Face scan and Liveness validation to check into scheduled session.
        </p>
      </div>

      {loading ? (
        <div className="flex h-60 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : !session ? (
        <Card className="border-red-200 bg-red-50/50 dark:bg-red-950/20 dark:border-red-900">
          <CardContent className="flex items-center gap-3 p-6 text-red-800 dark:text-red-300">
            <ShieldAlert className="h-6 w-6" />
            <p className="font-semibold">{errorMsg || 'Failed to locate session.'}</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-3">
          {/* CAMERA SCANNER & CONTROL PANEL */}
          <div className="md:col-span-2 space-y-6">
            <Card className="overflow-hidden border-slate-200 dark:border-slate-800 bg-black relative rounded-2xl aspect-video flex items-center justify-center">
              {cameraActive ? (
                <>
                  <video
                    ref={videoRef}
                    className="w-full h-full object-cover scale-x-[-1]"
                    muted
                    playsInline
                  />
                  <canvas
                    ref={canvasRef}
                    style={{ display: "none" }}
                  />
                  {/* Dynamic Face Scan Target Circle Overlay */}
                  {verifying && (
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <div className="w-56 h-56 rounded-full border-4 border-dashed border-primary animate-spin" />
                      <div className="absolute w-60 h-60 rounded-full border-2 border-primary/40 animate-ping" />
                      <div className="absolute w-56 h-0.5 bg-primary/80 animate-bounce shadow-[0_0_10px_#3b82f6]" />
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center p-8 text-slate-400 space-y-4">
                  {successData ? (
                    <div className="bg-emerald-500/10 border border-emerald-500/25 p-6 rounded-2xl text-emerald-400 flex flex-col items-center gap-2 max-w-sm w-full text-left font-semibold text-xs space-y-2">
                      <div className="flex items-center gap-2 text-emerald-400 mx-auto mb-2">
                        <CheckCircle2 className="h-8 w-8" />
                        <span className="font-bold text-lg">✅ Attendance Submitted</span>
                      </div>
                      <div className="w-full border-t border-emerald-500/20 pt-2 space-y-1 text-slate-300">
                        <p>Attendance ID: <b className="text-white">{successData.attendance_id || successData.id}</b></p>
                        <p>GPS Verified: <b className="text-white">{successData.gps_status || 'Verified'}</b></p>
                        <p>Face Verified: <b className="text-white">{successData.verification_status || 'Verified'}</b></p>
                        <p>Verification Score: <b className="text-white">{successData.confidence_score ? `${(successData.confidence_score * 100).toFixed(0)}%` : 'N/A'}</b></p>
                        <p>Timestamp: <b className="text-white">{successData.timestamp || (successData.check_in_time ? new Date(successData.check_in_time).toLocaleString() : new Date().toLocaleString())}</b></p>
                      </div>
                      <Button className="mt-4 w-full" onClick={() => navigate('/attendance')}>Back to Sessions</Button>
                    </div>
                  ) : (
                    <>
                      <Camera className="h-12 w-12 mx-auto opacity-40 text-slate-500" />
                      <p className="text-sm font-semibold">Camera stream is disconnected.</p>
                      <Button onClick={startCamera} size="sm" variant="secondary" className="rounded-xl">Activate Camera</Button>
                    </>
                  )}
                </div>
              )}
            </Card>

            {capturedImage && (
              <Card className="border-slate-200 dark:border-slate-800 p-4 rounded-2xl shadow-sm bg-white dark:bg-slate-900">
                <CardHeader className="p-0 pb-3">
                  <CardTitle className="text-xs font-black uppercase tracking-wider text-slate-500">Captured Selfie</CardTitle>
                </CardHeader>
                <CardContent className="p-0 flex items-center justify-center bg-slate-50 dark:bg-slate-950 rounded-xl overflow-hidden aspect-video relative max-w-sm mx-auto">
                  <img src={capturedImage} alt="Captured Selfie" className="w-full h-full object-cover" />
                </CardContent>
              </Card>
            )}

            {/* GPS Status Card */}
            <Card className="border-slate-200 dark:border-slate-800 p-4 rounded-2xl shadow-sm bg-white dark:bg-slate-900">
              <CardHeader className="p-0 pb-3 flex flex-row items-center justify-between">
                <CardTitle className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                  <MapPin className="h-4.5 w-4.5 text-primary" /> GPS Status
                </CardTitle>
                <span className="text-xs font-bold flex items-center gap-1">
                  {location ? (
                    <>
                      <span className="text-emerald-550">🟢</span> GPS Ready
                    </>
                  ) : (
                    <>
                      <span className="text-red-500">🔴</span> GPS Not Available
                    </>
                  )}
                </span>
              </CardHeader>
              <CardContent className="p-0 grid grid-cols-3 gap-4 text-xs font-semibold text-slate-650 dark:text-slate-400">
                <div className="space-y-1">
                  <span className="text-[10px] text-slate-400 uppercase">Latitude</span>
                  <p className="font-bold text-slate-950 dark:text-white">{location ? location.latitude.toFixed(6) : 'N/A'}</p>
                </div>
                <div className="space-y-1">
                  <span className="text-[10px] text-slate-400 uppercase">Longitude</span>
                  <p className="font-bold text-slate-950 dark:text-white">{location ? location.longitude.toFixed(6) : 'N/A'}</p>
                </div>
                <div className="space-y-1">
                  <span className="text-[10px] text-slate-400 uppercase">Accuracy</span>
                  <p className="font-bold text-slate-950 dark:text-white">{location ? `${location.accuracy.toFixed(1)}m` : 'N/A'}</p>
                </div>
              </CardContent>
            </Card>

            {/* TEST INFERENCE SIMULATOR CONTROLS */}
            <Card className="border-slate-200 dark:border-slate-850 rounded-2xl">
              <CardHeader className="py-4 border-b">
                <CardTitle className="text-xs font-black uppercase tracking-wider text-slate-500 flex items-center gap-2">
                  <Sliders className="h-4 w-4 text-indigo-500" /> AI Inference Simulator Console
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 grid gap-4 sm:grid-cols-3">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-slate-400 uppercase">GPS Geofence</label>
                  <select
                    value={gpsSimValid ? 'inside' : 'outside'}
                    onChange={(e) => setGpsSimValid(e.target.value === 'inside')}
                    className="w-full h-10 px-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs"
                  >
                    <option value="inside">Inside Boundary (Success)</option>
                    <option value="outside">Outside Boundary (Reject)</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-slate-400 uppercase">Face Match Score ({(simConfidence*100).toFixed(0)}%)</label>
                  <input
                    type="range"
                    min="0.5"
                    max="1.0"
                    step="0.05"
                    value={simConfidence}
                    onChange={(e) => setSimConfidence(parseFloat(e.target.value))}
                    className="w-full h-2 rounded-lg bg-slate-200 accent-primary"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] font-bold text-slate-400 uppercase">Spoof Anti-Spoof check</label>
                  <select
                    value={simLiveness}
                    onChange={(e) => setSimLiveness(e.target.value)}
                    className="w-full h-10 px-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs"
                  >
                    <option value="None">None (Genuine Scan)</option>
                    <option value="Static Photo">Static Photo Spoof</option>
                    <option value="Replay Attempt">Screen Replay spoof</option>
                    <option value="Multiple Faces">Multiple Faces</option>
                    <option value="Low Lighting">Low Lighting warning</option>
                  </select>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* VERIFICATION PIPELINE SIDE PANEL */}
          <div className="space-y-6">
            <Card className="border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm bg-white dark:bg-slate-900">
              <CardHeader className="pb-4">
                <CardTitle className="text-base font-bold text-slate-900 dark:text-white">Verification Status</CardTitle>
                <CardDescription className="text-xs text-slate-400">Pipeline logs in real-time.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* PIPELINE LOG LIST */}
                <div className="space-y-3.5">
                  {steps.map((step, idx) => (
                    <div key={idx} className="flex items-center justify-between text-xs font-semibold">
                      <span className={`${
                        step.status === 'success' ? 'text-emerald-500 font-bold' :
                        step.status === 'fail' ? 'text-red-500 font-bold' :
                        step.status === 'pending' ? 'text-primary font-bold animate-pulse' :
                        'text-slate-400'
                      }`}>{step.name}</span>

                      {step.status === 'success' && <CheckCircle2 className="h-4 w-4 text-emerald-500" />}
                      {step.status === 'fail' && <ShieldAlert className="h-4 w-4 text-red-500" />}
                      {step.status === 'pending' && <Loader2 className="h-4 w-4 animate-spin text-primary" />}
                      {step.status === 'idle' && <div className="h-3 w-3 rounded-full bg-slate-200 dark:bg-slate-800" />}
                    </div>
                  ))}
                </div>

                {/* ERROR OUTPUT */}
                {errorMsg && (
                  <div className="mt-4 p-3 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900 rounded-xl text-xs text-red-650 flex flex-col gap-1">
                    <span className="font-bold flex items-center gap-1"><AlertTriangle className="h-3.5 w-3.5 text-red-500" /> Pipeline Rejected:</span>
                    <p>{errorMsg}</p>
                    {session.fallback_policy === 'CoordinatorApproval' && errorMsg.includes('Face verification') && (
                      <div className="mt-2 text-[10px] text-amber-600 border-t border-red-200/50 pt-2 font-bold">
                        ⚠️ Fallback Triggered: Attendance marked as 'Pending Approval' instead of outright block.
                      </div>
                    )}
                  </div>
                )}

                {/* ACTIONS */}
                <div className="pt-4 border-t border-slate-100 dark:border-slate-800 flex flex-col gap-2.5">
                  <Button
                    onClick={runVerification}
                    disabled={!cameraActive || verifying}
                    className="w-full rounded-xl gap-2 font-bold"
                  >
                    {verifying ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Scanning Biometrics...
                      </>
                    ) : (
                      <>
                        <UserCheck className="h-4 w-4" />
                        Scan & Verify Face
                      </>
                    )}
                  </Button>
                  <Button variant="outline" className="w-full rounded-xl gap-1.5" onClick={() => navigate('/attendance')}>
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Session Metadata Card */}
            <Card className="bg-slate-50/50 dark:bg-slate-950/20 border-slate-150 dark:border-slate-850 rounded-2xl p-4 space-y-2">
              <h5 className="text-xs font-bold text-slate-400 uppercase">Target Session</h5>
              <p className="font-black text-sm text-slate-855 dark:text-white">{session.name}</p>
              <div className="text-[11px] text-slate-450 space-y-1">
                <p>Type: <b>{session.session_type}</b></p>
                <p>GPS radius limit: <b>{session.gps_radius ? `${session.gps_radius}m` : 'Disabled'}</b></p>
                <p>Match Threshold: <b>{((session.face_confidence_threshold || 0.85)*100).toFixed(0)}%</b></p>
                <p>Fallback Strategy: <b>{session.fallback_policy}</b></p>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
