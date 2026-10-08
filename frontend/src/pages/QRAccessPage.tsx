import React, { useState, useEffect } from 'react';
import { ShieldCheck, Activity, AlertTriangle, CheckCircle, Clock, ArrowLeft, Lock } from 'lucide-react';
import { api } from '../services/api';
import { QRAccessSummary } from '../types';

interface QRAccessPageProps {
  token: string;
  onBack: () => void;
}

export const QRAccessPage: React.FC<QRAccessPageProps> = ({ token, onBack }) => {
  const [data, setData] = useState<QRAccessSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRecord();
  }, [token]);

  const fetchRecord = async () => {
    setLoading(true);
    setError(null);
    try {
      const summary = await api.accessPatientByQR(token);
      setData(summary);
    } catch (err: any) {
      setError(err.message || 'Access token invalid or expired');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 text-center space-y-3">
        <div className="w-10 h-10 border-4 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-500">Verifying secure cryptographic access pass...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-md mx-auto px-4 py-16 text-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <h1 className="text-xl font-bold text-slate-900">Access Restricted</h1>
        <p className="text-xs text-slate-600 leading-relaxed bg-rose-50 border border-rose-200 p-3.5 rounded-2xl">
          {error || 'Unable to access digital record.'}
        </p>
        <button
          onClick={onBack}
          className="px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-slate-800 transition"
        >
          Return to Application
        </button>
      </div>
    );
  }

  const p = data.patient;
  const scr = data.latest_screening;
  const isHigh = scr?.risk_level?.includes('High');
  const isMod = scr?.risk_level?.includes('Moderate');

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="px-3.5 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 flex items-center space-x-1.5"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Exit Pass View</span>
        </button>

        <div className="flex items-center space-x-1.5 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full font-bold">
          <ShieldCheck className="w-4 h-4" />
          <span>Verified Digital Screening Pass</span>
        </div>
      </div>

      {/* Patient Header Card */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-3">
        <div className="flex items-start justify-between">
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Patient Record</span>
            <h1 className="text-xl font-bold text-slate-900">{p.name}</h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Code: <span className="font-mono font-semibold">{p.patient_code}</span> • {p.age}y / {p.gender}
            </p>
          </div>
          <div className="text-right text-[11px] text-slate-400">
            Pass Valid Until:<br />
            <span className="font-semibold text-slate-700">{new Date(data.token_expires_at).toLocaleString()}</span>
          </div>
        </div>

        {/* Clinical notes if available */}
        {(p.doctor_notes || p.referral_info || p.follow_up_instructions) && (
          <div className="pt-3 border-t border-slate-100 text-xs space-y-2">
            {p.doctor_notes && (
              <div>
                <span className="font-bold text-slate-700">Clinical Notes:</span>{' '}
                <span className="text-slate-600">{p.doctor_notes}</span>
              </div>
            )}
            {p.referral_info && (
              <div>
                <span className="font-bold text-slate-700">Referral:</span>{' '}
                <span className="text-slate-600">{p.referral_info}</span>
              </div>
            )}
            {p.follow_up_instructions && (
              <div>
                <span className="font-bold text-slate-700">Follow-up:</span>{' '}
                <span className="text-slate-600">{p.follow_up_instructions}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Screening Status Card */}
      {scr ? (
        <div
          className={`p-6 rounded-3xl border ${
            isHigh
              ? 'bg-rose-50 border-rose-200 text-rose-900'
              : isMod
              ? 'bg-amber-50 border-amber-200 text-amber-900'
              : 'bg-emerald-50 border-emerald-200 text-emerald-900'
          } space-y-4`}
        >
          <div className="flex items-center justify-between">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider opacity-75">
                AI-Assisted Preliminary Risk Level
              </span>
              <h2 className="text-2xl font-black">{scr.risk_level}</h2>
            </div>
            <div className="text-right">
              <span className="text-[10px] font-bold uppercase tracking-wider opacity-75 block">Risk Indicator</span>
              <span className="text-2xl font-black font-mono">{scr.risk_probability}%</span>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-2 text-xs">
            <div className="bg-white/70 p-2.5 rounded-xl border border-white/50">
              <span className="text-[10px] opacity-75 block">Confidence</span>
              <span className="font-black font-mono">{scr.confidence_level}</span>
            </div>
            <div className="bg-white/70 p-2.5 rounded-xl border border-white/50">
              <span className="text-[10px] opacity-75 block">Data Quality</span>
              <span className="font-black font-mono">{scr.data_quality}</span>
            </div>
            <div className="bg-white/70 p-2.5 rounded-xl border border-white/50">
              <span className="text-[10px] opacity-75 block">Left Knee ROM</span>
              <span className="font-black font-mono">{scr.left_knee_rom}°</span>
            </div>
            <div className="bg-white/70 p-2.5 rounded-xl border border-white/50">
              <span className="text-[10px] opacity-75 block">Gait Symmetry</span>
              <span className="font-black font-mono">{scr.gait_symmetry}%</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-3xl border border-slate-200 p-6 text-center text-xs text-slate-400">
          No active screening session on record yet.
        </div>
      )}

      {/* Safety Notice Callout */}
      <div className="bg-slate-100 border border-slate-200 p-4 rounded-2xl text-[11px] text-slate-600 leading-relaxed space-y-1">
        <p className="font-bold text-slate-800">Medical Safety Notice:</p>
        <p>{data.disclaimer}</p>
      </div>
    </div>
  );
};
