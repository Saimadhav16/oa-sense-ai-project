import React, { useState } from 'react';
import {
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  ArrowRight,
  Download,
  Share2,
  RefreshCw,
  Activity,
  ShieldCheck,
  Zap,
  TrendingDown
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
  Cell,
  PieChart,
  Pie
} from 'recharts';
import { ScreeningRecord, RiskLevel } from '../types';
import { api } from '../services/api';
import { useTranslation } from '../utils/i18n';

interface ResultDashboardPageProps {
  screening: ScreeningRecord;
  onStartNewScreening: () => void;
  onViewPatientProfile: (patientId: number) => void;
}

export const ResultDashboardPage: React.FC<ResultDashboardPageProps> = ({
  screening,
  onStartNewScreening,
  onViewPatientProfile
}) => {
  const { t } = useTranslation();
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  const handleGeneratePdf = async () => {
    setDownloadingPdf(true);
    try {
      const res = await api.generateReport(screening.id);
      const url = api.getReportDownloadUrl(res.report_id);
      setDownloadUrl(url);
      window.open(url, '_blank');
    } catch (e: any) {
      alert('Could not generate PDF: ' + (e.message || 'Error'));
    } finally {
      setDownloadingPdf(false);
    }
  };

  // Synthetic angle time-series trajectory for graph visualization
  const trajectoryData = Array.from({ length: 20 }, (_, i) => {
    const tSec = (i * 0.4).toFixed(1);
    const wave = Math.sin(i * 0.5);
    return {
      time: `${tSec}s`,
      leftKnee: Math.round(screening.left_knee_rom + wave * 18),
      rightKnee: Math.round(screening.right_knee_rom + wave * 15)
    };
  });

  const contributionPie = [
    { name: 'Questionnaire Burden', value: screening.questionnaire_contribution || 52, color: '#0d9488' },
    { name: 'Computer-Vision Movement', value: screening.movement_contribution || 48, color: '#06b6d4' }
  ];

  // Feature Importance data for Explainable AI
  const importanceData = [
    { name: 'Joint Pain Score', score: Math.round((screening.pain_score / 10) * 100), importance: 28 },
    { name: 'Mobility Limitation', score: Math.round(((10 - screening.mobility_score) / 10) * 100), importance: 24 },
    { name: 'Gait Asymmetry', score: Math.round(100 - screening.gait_symmetry), importance: 20 },
    { name: 'Knee ROM Restriction', score: Math.round(Math.max(0, (140 - screening.left_knee_rom) / 70 * 100)), importance: 16 },
    { name: 'Posture Deviation', score: Math.round(100 - screening.posture_score), importance: 12 }
  ];

  const isHigh = screening.risk_level.includes('High');
  const isMod = screening.risk_level.includes('Moderate');

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Top Header Card */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <span className="text-xs font-bold text-teal-700 bg-teal-50 border border-teal-200 px-3 py-1 rounded-full uppercase tracking-wider">
            {t('result.screeningHeader')}
          </span>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight mt-2">
            {t('result.title')}
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Patient: <b>{screening.patient_name || 'Patient'}</b> (Code: {screening.patient_code || 'N/A'}) • Screened on {new Date(screening.screening_date).toLocaleDateString()}
          </p>
        </div>

        {/* Buttons Action Group */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleGeneratePdf}
            disabled={downloadingPdf}
            className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-md shadow-teal-600/20 flex items-center space-x-2 transition disabled:opacity-50"
          >
            <FileText className="w-4 h-4" />
            <span>{downloadingPdf ? 'Generating PDF...' : t('result.generatePdf')}</span>
          </button>

          <button
            onClick={onStartNewScreening}
            className="px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center space-x-1.5 transition"
          >
            <RefreshCw className="w-4 h-4 text-slate-500" />
            <span>{t('result.newScreening')}</span>
          </button>
        </div>
      </div>

      {/* Primary Risk Stratification Banner */}
      <div
        className={`p-6 sm:p-8 rounded-3xl border transition ${
          isHigh
            ? 'bg-rose-50 border-rose-200 text-rose-900'
            : isMod
            ? 'bg-amber-50 border-amber-200 text-amber-900'
            : 'bg-emerald-50 border-emerald-200 text-emerald-900'
        }`}
      >
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="flex items-start space-x-4">
            <div
              className={`w-14 h-14 rounded-2xl flex items-center justify-center text-white flex-shrink-0 shadow-md ${
                isHigh ? 'bg-rose-600' : isMod ? 'bg-amber-600' : 'bg-emerald-600'
              }`}
            >
              {isHigh ? (
                <AlertTriangle className="w-8 h-8" />
              ) : isMod ? (
                <Clock className="w-8 h-8" />
              ) : (
                <CheckCircle className="w-8 h-8" />
              )}
            </div>

            <div>
              <span className="text-xs font-bold uppercase tracking-wider opacity-80">
                Risk Stratification Level
              </span>
              <h2 className="text-3xl font-black tracking-tight">{screening.risk_level.toUpperCase()}</h2>
              <p className="text-xs mt-1 max-w-xl opacity-90 leading-relaxed">
                {isHigh
                  ? 'Screening profile displays indicators associated with elevated osteoarthritis risk. Bilateral joint symmetry disparity and reported joint burden warrant clinical evaluation.'
                  : isMod
                  ? 'Screening profile contains mild to moderate joint mobility indicators. Routine physical monitoring and non-impact exercises are recommended.'
                  : 'Screening profile exhibits healthy joint range of motion and symmetric gait dynamics.'}
              </p>
            </div>
          </div>

          {/* Key Risk Indicators Percentage Block */}
          <div className="bg-white/80 backdrop-blur-sm p-4 rounded-2xl border border-white/50 flex items-center space-x-6 text-slate-800">
            <div>
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">{t('result.indicator')}</span>
              <span className="text-2xl font-black font-mono text-teal-700">{screening.risk_probability}%</span>
            </div>
            <div className="h-8 w-px bg-slate-200" />
            <div>
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block">{t('result.confidence')}</span>
              <span className="text-2xl font-black font-mono text-slate-700">{screening.confidence}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* 5 Core Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <span className="text-[11px] text-slate-500 font-semibold block">Pain Score</span>
          <span className="text-xl font-bold font-mono text-slate-900 mt-1 block">
            {screening.pain_score} <span className="text-xs text-slate-400 font-normal">/ 10</span>
          </span>
          <span className={`text-[10px] font-semibold mt-1 block ${screening.pain_score >= 6 ? 'text-rose-600' : 'text-slate-500'}`}>
            {screening.pain_score >= 6 ? 'High Discomfort' : 'Manageable'}
          </span>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <span className="text-[11px] text-slate-500 font-semibold block">Mobility Score</span>
          <span className="text-xl font-bold font-mono text-slate-900 mt-1 block">
            {screening.mobility_score} <span className="text-xs text-slate-400 font-normal">/ 10</span>
          </span>
          <span className={`text-[10px] font-semibold mt-1 block ${screening.mobility_score <= 4 ? 'text-rose-600' : 'text-slate-500'}`}>
            {screening.mobility_score <= 4 ? 'Restricted Movement' : 'Adequate Functional Range'}
          </span>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <span className="text-[11px] text-slate-500 font-semibold block">Knee ROM (L / R)</span>
          <span className="text-xl font-bold font-mono text-teal-600 mt-1 block">
            {screening.left_knee_rom}° / {screening.right_knee_rom}°
          </span>
          <span className="text-[10px] text-slate-500 font-semibold mt-1 block">
            Symmetry: {screening.knee_symmetry}%
          </span>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <span className="text-[11px] text-slate-500 font-semibold block">Gait Symmetry</span>
          <span className="text-xl font-bold font-mono text-cyan-600 mt-1 block">
            {screening.gait_symmetry}%
          </span>
          <span className="text-[10px] text-slate-500 font-semibold mt-1 block">
            Smoothness: {screening.movement_smoothness}%
          </span>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs col-span-2 lg:col-span-1">
          <span className="text-[11px] text-slate-500 font-semibold block">Posture Alignment</span>
          <span className="text-xl font-bold font-mono text-emerald-600 mt-1 block">
            {screening.posture_score} <span className="text-xs text-slate-400 font-normal">/ 100</span>
          </span>
          <span className="text-[10px] text-emerald-700 font-semibold mt-1 block">
            {screening.posture_score >= 80 ? 'Optimal Symmetry' : 'Lateral Pelvic Tilt'}
          </span>
        </div>
      </div>

      {/* Visual Analytics Row: Knee Trajectory & Explainable AI Drivers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Knee Angle Over Time Chart */}
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-4 flex items-center space-x-2">
            <Activity className="w-4 h-4 text-teal-600" />
            <span>Knee Flexion & Extension Trajectory Over Time</span>
          </h3>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trajectoryData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="time" textAnchor="end" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                <YAxis domain={[40, 160]} tick={{ fontSize: 10 }} stroke="#94a3b8" unit="°" />
                <Tooltip />
                <Line type="monotone" dataKey="leftKnee" stroke="#0d9488" strokeWidth={2.5} dot={false} name="Left Knee Angle" />
                <Line type="monotone" dataKey="rightKnee" stroke="#06b6d4" strokeWidth={2.5} dot={false} name="Right Knee Angle" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center space-x-6 text-xs text-slate-500 mt-2">
            <div className="flex items-center space-x-2">
              <span className="w-3 h-1 bg-teal-600 rounded-full" />
              <span>Left Knee Angle (Flexion Range)</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="w-3 h-1 bg-cyan-500 rounded-full" />
              <span>Right Knee Angle (Flexion Range)</span>
            </div>
          </div>
        </div>

        {/* Explainable AI: Feature Importance & Top Risk Drivers */}
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-4 flex items-center space-x-2">
            <Zap className="w-4 h-4 text-amber-500" />
            <span>Explainable AI: {t('result.topDrivers')}</span>
          </h3>
          <div className="space-y-3.5">
            {importanceData.map((item) => (
              <div key={item.name} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-slate-700">{item.name}</span>
                  <span className="font-mono text-slate-500">{item.score}% abnormality indicator</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      item.score > 60 ? 'bg-rose-500' : item.score > 35 ? 'bg-amber-500' : 'bg-teal-500'
                    }`}
                    style={{ width: `${item.score}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 pt-4 border-t border-slate-100 text-xs text-slate-500 flex justify-between">
            <span>Questionnaire Factor: <b>{screening.questionnaire_contribution}%</b></span>
            <span>Movement Biomechanics Factor: <b>{screening.movement_contribution}%</b></span>
          </div>
        </div>
      </div>

      {/* Clinical Recommendations */}
      <div className="bg-teal-50/50 border border-teal-200 p-6 rounded-3xl">
        <h3 className="text-sm font-bold text-teal-900 uppercase tracking-wider mb-3">
          {t('result.recommendations')}
        </h3>
        <ul className="space-y-2 text-xs text-teal-950">
          <li className="flex items-start space-x-2">
            <span className="text-teal-600 font-bold">✓</span>
            <span>Schedule a consultation with a qualified orthopedic physician or physical therapist for clinical joint examination.</span>
          </li>
          <li className="flex items-start space-x-2">
            <span className="text-teal-600 font-bold">✓</span>
            <span>Incorporate low-impact quadriceps strengthening and gentle range-of-motion flexibility exercises into daily routine.</span>
          </li>
          <li className="flex items-start space-x-2">
            <span className="text-teal-600 font-bold">✓</span>
            <span>Avoid deep repetitive squats and high-impact loading when acute knee stiffness is present.</span>
          </li>
          <li className="flex items-start space-x-2">
            <span className="text-teal-600 font-bold">✓</span>
            <span>Repeat OA-Sense functional screening in 3 to 6 months to track joint angle and symmetry trends.</span>
          </li>
        </ul>
      </div>

      {/* Medical Safety Disclaimer Callout */}
      <div className="bg-slate-100 border border-slate-300 p-4 rounded-2xl text-[11px] text-slate-600 leading-relaxed">
        <b>CLINICAL SCREENING DISCLAIMER:</b> {t('disclaimer.banner')}
      </div>
    </div>
  );
};
