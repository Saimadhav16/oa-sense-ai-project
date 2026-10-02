import React, { useState, useEffect } from 'react';
import { FileText, Download, Search, CheckCircle, Clock, AlertTriangle } from 'lucide-react';
import { ScreeningRecord } from '../types';
import { api } from '../services/api';
import { useTranslation } from '../utils/i18n';

interface ReportsPageProps {
  onSelectScreening: (screening: ScreeningRecord) => void;
}

export const ReportsPage: React.FC<ReportsPageProps> = ({ onSelectScreening }) => {
  const { t } = useTranslation();
  const [screenings, setScreenings] = useState<ScreeningRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [generatingId, setGeneratingId] = useState<number | null>(null);

  useEffect(() => {
    loadScreenings();
  }, []);

  const loadScreenings = async () => {
    setLoading(true);
    try {
      const data = await api.getScreenings();
      setScreenings(data);
    } catch (e) {
      console.warn('Error loading screenings:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = async (s: ScreeningRecord) => {
    setGeneratingId(s.id);
    try {
      const res = await api.generateReport(s.id);
      const url = api.getReportDownloadUrl(res.report_id);
      window.open(url, '_blank');
    } catch (e: any) {
      alert('PDF generation error: ' + (e.message || 'Error'));
    } finally {
      setGeneratingId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">Screening Reports Archive</h1>
        <p className="text-xs text-slate-500 mt-1">
          Exportable preliminary assessment PDF documentation for clinical records
        </p>
      </div>

      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                <th className="py-3 px-6">Date</th>
                <th className="py-3 px-6">Patient</th>
                <th className="py-3 px-6">Risk Stratification</th>
                <th className="py-3 px-6">Pain / Mobility</th>
                <th className="py-3 px-6">Knee ROM</th>
                <th className="py-3 px-6 text-right">PDF Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {screenings.map((s) => {
                const isHigh = s.risk_level?.includes('High');
                const isMod = s.risk_level?.includes('Moderate');
                return (
                  <tr key={s.id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3.5 px-6 text-xs text-slate-500">
                      {new Date(s.screening_date).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-6 font-semibold text-slate-900">
                      {s.patient_name} <span className="font-mono text-xs text-slate-400 font-normal">({s.patient_code})</span>
                    </td>
                    <td className="py-3.5 px-6">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${
                          isHigh
                            ? 'bg-rose-100 text-rose-800'
                            : isMod
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {s.risk_level} ({s.risk_probability}%)
                      </span>
                    </td>
                    <td className="py-3.5 px-6 text-xs text-slate-600">
                      Pain: {s.pain_score}/10 • Mobility: {s.mobility_score}/10
                    </td>
                    <td className="py-3.5 px-6 text-xs font-mono text-teal-700 font-semibold">
                      {s.left_knee_rom}° / {s.right_knee_rom}°
                    </td>
                    <td className="py-3.5 px-6 text-right space-x-2">
                      <button
                        onClick={() => onSelectScreening(s)}
                        className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold transition"
                      >
                        Review
                      </button>
                      <button
                        onClick={() => handleDownloadPdf(s)}
                        disabled={generatingId === s.id}
                        className="px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold transition inline-flex items-center space-x-1 disabled:opacity-50"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>{generatingId === s.id ? 'Generating...' : 'PDF'}</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
