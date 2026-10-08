import React, { useState, useEffect } from 'react';
import {
  User,
  Calendar,
  PlusCircle,
  ArrowLeft,
  Activity,
  FileText,
  CheckCircle,
  AlertTriangle,
  Clock,
  QrCode,
  ShieldCheck,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Minus,
  Edit3,
  Save,
  XCircle,
  ExternalLink
} from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Patient, ScreeningRecord, RiskTrajectory, QRPassRecord } from '../types';
import { api } from '../services/api';
import { useTranslation } from '../utils/i18n';

interface PatientProfilePageProps {
  patientId: number;
  onBack: () => void;
  onStartScreening: (patient: Patient) => void;
  onViewScreening: (screening: ScreeningRecord) => void;
}

export const PatientProfilePage: React.FC<PatientProfilePageProps> = ({
  patientId,
  onBack,
  onStartScreening,
  onViewScreening
}) => {
  const { t } = useTranslation();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [screenings, setScreenings] = useState<ScreeningRecord[]>([]);
  const [trajectory, setTrajectory] = useState<RiskTrajectory | null>(null);
  const [qrPasses, setQrPasses] = useState<QRPassRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Notes editing state
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [doctorNotes, setDoctorNotes] = useState('');
  const [referralInfo, setReferralInfo] = useState('');
  const [followUp, setFollowUp] = useState('');
  const [savingNotes, setSavingNotes] = useState(false);

  // QR Modal / Active Pass state
  const [activeQrModal, setActiveQrModal] = useState<{
    url: string;
    expiresAt: string;
    tokenString: string;
  } | null>(null);
  const [generatingQr, setGeneratingQr] = useState(false);

  useEffect(() => {
    loadProfile();
  }, [patientId]);

  const loadProfile = async () => {
    setLoading(true);
    try {
      const data = await api.getPatientById(patientId);
      setPatient(data.patient);
      setScreenings(data.screenings || []);
      setDoctorNotes(data.patient.doctor_notes || '');
      setReferralInfo(data.patient.referral_info || '');
      setFollowUp(data.patient.follow_up_instructions || '');

      // Load trajectory
      try {
        const trajRes = await api.getPatientTrajectory(patientId);
        setTrajectory(trajRes.trajectory);
      } catch (e) {
        console.warn('Trajectory fetch error:', e);
      }

      if (data.qr_passes) {
        setQrPasses(data.qr_passes);
      }
    } catch (e) {
      console.warn('Error loading patient:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveNotes = async () => {
    if (!patient) return;
    setSavingNotes(true);
    try {
      const updated = await api.updatePatient(patient.id, {
        doctor_notes: doctorNotes,
        referral_info: referralInfo,
        follow_up_instructions: followUp
      });
      setPatient(updated);
      setIsEditingNotes(false);
    } catch (err: any) {
      alert('Failed to update notes: ' + err.message);
    } finally {
      setSavingNotes(false);
    }
  };

  const handleGenerateQR = async () => {
    if (!patient) return;
    setGeneratingQr(true);
    try {
      const res = await api.generatePatientQR(patient.id, 72);
      // Safe URL resolution priority:
      // 1. Explicit configured public URL if available (VITE_PUBLIC_APP_URL)
      // 2. If opened using a non-loopback hostname/IP, use current application origin
      // 3. Fallback to LAN configuration if running on localhost/loopback
      const configuredPublicUrl = (import.meta.env.VITE_PUBLIC_APP_URL as string)?.trim().replace(/\/$/, '');
      let baseOrigin = window.location.origin;
      const hostname = window.location.hostname;

      if (configuredPublicUrl) {
        baseOrigin = configuredPublicUrl;
      } else if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '0.0.0.0') {
        // In local development on loopback, if no env URL set, provide LAN fallback IP if configured,
        // otherwise warn or use origin.
        baseOrigin = window.location.origin;
      }

      const fullUrl = `${baseOrigin}${res.access_url}`;
      setActiveQrModal({
        url: fullUrl,
        expiresAt: res.expires_at,
        tokenString: res.access_url.replace('/access/', '')
      });
      // Refresh passes list
      await loadProfile();
    } catch (e: any) {
      alert('Could not generate QR: ' + e.message);
    } finally {
      setGeneratingQr(false);
    }
  };

  const handleRevokeQR = async (qrId: number) => {
    if (!confirm('Are you sure you want to revoke this QR access pass? Scanners will no longer be able to read this record.')) return;
    try {
      await api.revokePatientQR(qrId);
      await loadProfile();
      if (activeQrModal) setActiveQrModal(null);
    } catch (e: any) {
      alert('Failed to revoke QR: ' + e.message);
    }
  };

  const trendData = screenings.map((s) => ({
    date: new Date(s.screening_date).toLocaleDateString(),
    painScore: s.pain_score,
    mobilityScore: s.mobility_score,
    kneeRom: s.left_knee_rom
  })).reverse();

  if (loading || !patient) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center text-slate-500 text-sm">
        Loading patient medical profile...
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      {/* Top Action Bar */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="px-4 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center space-x-1.5 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </button>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleGenerateQR}
            disabled={generatingQr}
            className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold flex items-center space-x-1.5 transition shadow-sm"
          >
            <QrCode className="w-4 h-4 text-teal-400" />
            <span>{generatingQr ? 'Generating...' : 'Issue Secure QR Pass'}</span>
          </button>

          <button
            onClick={() => onStartScreening(patient)}
            className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-md shadow-teal-600/20 flex items-center space-x-1.5 transition"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Start New Screening</span>
          </button>
        </div>
      </div>

      {/* Patient Bio & Digital Record Card */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-xs flex flex-col md:flex-row justify-between gap-6">
        <div className="flex items-start space-x-4">
          <div className="w-16 h-16 rounded-2xl bg-teal-600 text-white flex items-center justify-center text-xl font-black shadow-md shadow-teal-600/20">
            {patient.name.charAt(0)}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-slate-900">{patient.name}</h1>
              <span className="font-mono text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                {patient.patient_code}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {patient.age} years old • {patient.gender} • Occupation: {patient.occupation || 'N/A'}
            </p>
            <p className="text-xs text-slate-500">
              Location: {patient.location || 'Rural Centre'} • Activity: {patient.activity_level}
            </p>
            <p className="text-[11px] text-slate-400 mt-1">
              Record registered: {new Date(patient.created_at).toLocaleDateString()}
              {patient.updated_at && ` • Last updated: ${new Date(patient.updated_at).toLocaleDateString()}`}
            </p>
          </div>
        </div>

        {/* Clinical Factors Quick Tags */}
        <div className="flex flex-wrap gap-1.5 max-w-sm">
          {patient.joint_injury === 1 && (
            <span className="px-2.5 py-1 rounded-lg bg-rose-50 text-rose-800 border border-rose-200 text-[11px] font-semibold">
              Prior Knee Injury
            </span>
          )}
          {patient.family_history === 1 && (
            <span className="px-2.5 py-1 rounded-lg bg-amber-50 text-amber-800 border border-amber-200 text-[11px] font-semibold">
              Family OA History
            </span>
          )}
          {patient.demanding_work === 1 && (
            <span className="px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-800 border border-indigo-200 text-[11px] font-semibold">
              Heavy Physical Labor
            </span>
          )}
          {patient.morning_stiffness === 1 && (
            <span className="px-2.5 py-1 rounded-lg bg-purple-50 text-purple-800 border border-purple-200 text-[11px] font-semibold">
              Morning Stiffness
            </span>
          )}
        </div>
      </div>

      {/* Doctor / Healthcare-Worker Clinical Notes & Referral */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-teal-600" />
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Healthcare Professional Clinical Notes & Referral Details
            </h2>
          </div>
          {!isEditingNotes ? (
            <button
              onClick={() => setIsEditingNotes(true)}
              className="text-xs font-semibold text-teal-600 hover:text-teal-700 flex items-center space-x-1"
            >
              <Edit3 className="w-3.5 h-3.5" />
              <span>Edit Notes</span>
            </button>
          ) : (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsEditingNotes(false)}
                className="text-xs font-semibold text-slate-500 hover:text-slate-600 px-2 py-1"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveNotes}
                disabled={savingNotes}
                className="text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white px-3 py-1 rounded-lg flex items-center space-x-1"
              >
                <Save className="w-3.5 h-3.5" />
                <span>{savingNotes ? 'Saving...' : 'Save'}</span>
              </button>
            </div>
          )}
        </div>

        {isEditingNotes ? (
          <div className="space-y-3 pt-1">
            <div>
              <label className="text-[11px] font-semibold text-slate-700 block mb-1">Doctor / Healthcare Worker Notes:</label>
              <textarea
                value={doctorNotes}
                onChange={(e) => setDoctorNotes(e.target.value)}
                placeholder="Enter clinical examination notes or symptoms..."
                className="w-full text-xs p-2.5 rounded-xl border border-slate-300 focus:outline-teal-600"
                rows={2}
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] font-semibold text-slate-700 block mb-1">Referral Information:</label>
                <input
                  type="text"
                  value={referralInfo}
                  onChange={(e) => setReferralInfo(e.target.value)}
                  placeholder="e.g., Referred to District Orthopedic Clinic"
                  className="w-full text-xs p-2 rounded-xl border border-slate-300 focus:outline-teal-600"
                />
              </div>
              <div>
                <label className="text-[11px] font-semibold text-slate-700 block mb-1">Follow-up Instructions:</label>
                <input
                  type="text"
                  value={followUp}
                  onChange={(e) => setFollowUp(e.target.value)}
                  placeholder="e.g., Re-screen in 3 months; knee strengthening exercises"
                  className="w-full text-xs p-2 rounded-xl border border-slate-300 focus:outline-teal-600"
                />
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
            <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Clinical Notes</span>
              <p className="text-xs text-slate-700 mt-1 leading-relaxed">
                {patient.doctor_notes || 'No clinical notes recorded yet.'}
              </p>
            </div>
            <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Referral Info</span>
              <p className="text-xs text-slate-700 mt-1 leading-relaxed">
                {patient.referral_info || 'No referral recorded.'}
              </p>
            </div>
            <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Follow-up Instructions</span>
              <p className="text-xs text-slate-700 mt-1 leading-relaxed">
                {patient.follow_up_instructions || 'Standard routine re-screening recommended.'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Phase 6: OA Risk-Marker Trajectory Section */}
      {trajectory && (
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-teal-600" />
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                OA Risk-Marker Longitudinal Trajectory
              </h2>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-500">Status:</span>
              <span
                className={`px-3 py-0.5 rounded-full text-xs font-bold ${
                  trajectory.status === 'Improving'
                    ? 'bg-emerald-100 text-emerald-800'
                    : trajectory.status === 'Worsening'
                    ? 'bg-rose-100 text-rose-800'
                    : 'bg-teal-100 text-teal-800'
                }`}
              >
                {trajectory.status}
              </span>
            </div>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3.5 rounded-2xl border border-slate-200">
            {trajectory.summary}
          </p>

          {trajectory.comparison && trajectory.comparison.sessions_compared > 1 && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-center">
                <span className="text-[10px] text-slate-400 font-semibold block">ROM Change</span>
                <span className={`text-base font-black font-mono mt-0.5 block ${
                  trajectory.comparison.rom_change >= 0 ? 'text-emerald-600' : 'text-rose-600'
                }`}>
                  {trajectory.comparison.rom_change > 0 ? `+${trajectory.comparison.rom_change}°` : `${trajectory.comparison.rom_change}°`}
                </span>
              </div>
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-center">
                <span className="text-[10px] text-slate-400 font-semibold block">Pain Score Change</span>
                <span className={`text-base font-black font-mono mt-0.5 block ${
                  trajectory.comparison.pain_change <= 0 ? 'text-emerald-600' : 'text-rose-600'
                }`}>
                  {trajectory.comparison.pain_change > 0 ? `+${trajectory.comparison.pain_change}` : `${trajectory.comparison.pain_change}`}
                </span>
              </div>
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-center">
                <span className="text-[10px] text-slate-400 font-semibold block">Symmetry Change</span>
                <span className={`text-base font-black font-mono mt-0.5 block ${
                  trajectory.comparison.symmetry_change >= 0 ? 'text-emerald-600' : 'text-rose-600'
                }`}>
                  {trajectory.comparison.symmetry_change > 0 ? `+${trajectory.comparison.symmetry_change}%` : `${trajectory.comparison.symmetry_change}%`}
                </span>
              </div>
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-center">
                <span className="text-[10px] text-slate-400 font-semibold block">Sessions Compared</span>
                <span className="text-base font-black font-mono text-slate-800 mt-0.5 block">
                  {trajectory.comparison.sessions_compared}
                </span>
              </div>
            </div>
          )}

          {trendData.length > 1 && (
            <div className="h-48 pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                  <YAxis tick={{ fontSize: 10 }} stroke="#94a3b8" />
                  <Tooltip />
                  <Line type="monotone" dataKey="painScore" stroke="#ef4444" strokeWidth={2} name="Pain Score (0-10)" />
                  <Line type="monotone" dataKey="mobilityScore" stroke="#10b981" strokeWidth={2} name="Mobility (0-10)" />
                  <Line type="monotone" dataKey="kneeRom" stroke="#0d9488" strokeWidth={2} name="Left Knee ROM (°)" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* QR Passes Management Section */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-2">
            <QrCode className="w-4 h-4 text-teal-600" />
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Secure QR Digital Record Passes
            </h2>
          </div>
          <span className="text-[11px] text-slate-400 font-medium">
            Zero PHI in QR • Opaque tokens with audit logging
          </span>
        </div>

        {qrPasses.length > 0 ? (
          <div className="space-y-2.5">
            {qrPasses.map((qr) => {
              const isExpired = new Date() > new Date(qr.expires_at);
              return (
                <div
                  key={qr.id}
                  className="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                >
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-slate-800">Pass #{qr.id}</span>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          qr.is_revoked
                            ? 'bg-rose-100 text-rose-800'
                            : isExpired
                            ? 'bg-slate-200 text-slate-700'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {qr.is_revoked ? 'REVOKED' : isExpired ? 'EXPIRED' : 'ACTIVE'}
                      </span>
                      <span className="text-[11px] text-slate-400">
                        Accessed {qr.access_count} times
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Expires: {new Date(qr.expires_at).toLocaleString()} • Created: {new Date(qr.created_at).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="flex items-center space-x-2 self-start sm:self-auto">
                    {!qr.is_revoked && !isExpired && (
                      <button
                        onClick={() => handleRevokeQR(qr.id)}
                        className="px-2.5 py-1 rounded-lg border border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100 text-[11px] font-semibold transition"
                      >
                        Revoke Pass
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-slate-400 py-2">
            No active QR access passes issued. Click "Issue Secure QR Pass" to generate an authorized access token.
          </p>
        )}
      </div>

      {/* Screening Timeline History */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-xs">
        <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-6 flex items-center space-x-2">
          <Calendar className="w-4 h-4 text-teal-600" />
          <span>Screening Session History Timeline</span>
        </h2>

        {screenings.length > 0 ? (
          <div className="relative border-l-2 border-slate-200 ml-4 space-y-6">
            {screenings.map((scr) => {
              const isHigh = scr.risk_level?.includes('High');
              const isMod = scr.risk_level?.includes('Moderate');
              return (
                <div key={scr.id} className="relative pl-6">
                  {/* Timeline Dot */}
                  <span
                    className={`absolute -left-2.5 top-1.5 w-5 h-5 rounded-full border-2 border-white flex items-center justify-center ${
                      isHigh ? 'bg-rose-600' : isMod ? 'bg-amber-500' : 'bg-emerald-600'
                    }`}
                  />

                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 hover:border-teal-300 transition flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold text-slate-800">
                          {new Date(scr.screening_date).toLocaleDateString()}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            isHigh
                              ? 'bg-rose-100 text-rose-800'
                              : isMod
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-emerald-100 text-emerald-800'
                          }`}
                        >
                          {scr.risk_level}
                        </span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700">
                          Conf: {scr.confidence_level || 'HIGH'}
                        </span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700">
                          Data: {scr.data_quality || 'GOOD'}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">
                        Risk: <b>{scr.risk_probability}%</b> • Pain: {scr.pain_score}/10 • Left ROM: {scr.left_knee_rom}° • Gait Symmetry: {scr.gait_symmetry}%
                      </p>
                    </div>

                    <button
                      onClick={() => onViewScreening(scr)}
                      className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-100 text-slate-700 text-xs font-semibold flex items-center space-x-1 self-start sm:self-auto transition"
                    >
                      <FileText className="w-3.5 h-3.5 text-slate-500" />
                      <span>View Results</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8 text-xs text-slate-400">
            No previous screenings recorded for this patient.
          </div>
        )}
      </div>

      {/* QR Code Presentation Modal */}
      {activeQrModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-sm w-full border border-slate-200 shadow-2xl text-center space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <span className="text-xs font-bold text-teal-700 uppercase tracking-wider">Secure Patient QR Pass</span>
              <button
                onClick={() => setActiveQrModal(null)}
                className="text-slate-400 hover:text-slate-600 text-sm"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-500">
              Patient: <b>{patient.name}</b> ({patient.patient_code})
            </p>

            <div className="flex justify-center p-4 bg-white rounded-2xl border-2 border-slate-200 shadow-inner">
              <QRCodeSVG
                value={activeQrModal.url}
                size={200}
                level="H"
                includeMargin={true}
              />
            </div>

            <div className="p-3 bg-slate-50 rounded-xl text-left text-[11px] text-slate-600 space-y-1">
              <div className="flex justify-between">
                <span>Expires at:</span>
                <span className="font-semibold">{new Date(activeQrModal.expiresAt).toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span>Security:</span>
                <span className="font-semibold text-emerald-600">Opaque Token Only</span>
              </div>
            </div>

            <div className="text-[10px] text-slate-400 leading-normal">
              Notice: This QR code embeds an authorized opaque access token. It contains zero medical details, questionnaire answers, or passwords.
            </div>

            <div className="text-[10px] text-teal-600 font-medium">
              Scan using a device connected to the same Wi-Fi network.
            </div>

            <button
              onClick={() => setActiveQrModal(null)}
              className="w-full py-2.5 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-slate-800 transition"
            >
              Done
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
