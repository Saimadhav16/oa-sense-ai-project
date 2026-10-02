import React, { useState, useEffect } from 'react';
import { User, Calendar, PlusCircle, ArrowLeft, Activity, FileText, CheckCircle, AlertTriangle, Clock } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Patient, ScreeningRecord } from '../types';
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
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadProfile();
  }, [patientId]);

  const loadProfile = async () => {
    setLoading(true);
    try {
      const data = await api.getPatientById(patientId);
      setPatient(data.patient);
      setScreenings(data.screenings);
    } catch (e) {
      console.warn('Error loading patient:', e);
    } finally {
      setLoading(false);
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

        <button
          onClick={() => onStartScreening(patient)}
          className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-md shadow-teal-600/20 flex items-center space-x-1.5 transition"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Start New Screening</span>
        </button>
      </div>

      {/* Patient Bio Card */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-xs flex flex-col md:flex-row justify-between gap-6">
        <div className="flex items-start space-x-4">
          <div className="w-16 h-16 rounded-2xl bg-teal-600 text-white flex items-center justify-center text-xl font-black shadow-md shadow-teal-600/20">
            {patient.name.charAt(0)}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-slate-900">{patient.name}</h1>
              <span className="font-mono text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded">
                {patient.patient_code}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {patient.age} years old • {patient.gender} • Occupation: {patient.occupation || 'N/A'}
            </p>
            <p className="text-xs text-slate-500">
              Location: {patient.location || 'Rural Centre'} • Activity: {patient.activity_level}
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

      {/* Longitudinal Trend Chart (if multiple screenings) */}
      {trendData.length > 1 && (
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
          <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-4 flex items-center space-x-2">
            <Activity className="w-4 h-4 text-teal-600" />
            <span>Screening Trajectory & Trend Across Sessions</span>
          </h2>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                <YAxis tick={{ fontSize: 10 }} stroke="#94a3b8" />
                <Tooltip />
                <Line type="monotone" dataKey="painScore" stroke="#ef4444" strokeWidth={2} name="Pain Score" />
                <Line type="monotone" dataKey="mobilityScore" stroke="#10b981" strokeWidth={2} name="Mobility Rating" />
                <Line type="monotone" dataKey="kneeRom" stroke="#0d9488" strokeWidth={2} name="Knee ROM (deg)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

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
    </div>
  );
};
