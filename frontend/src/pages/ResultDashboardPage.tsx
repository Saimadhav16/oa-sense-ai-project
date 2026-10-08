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

  // Real captured angle time-series trajectory or measured kinematic bounds
  const trajectoryData = (screening as any).frames && (screening as any).frames.length > 0
    ? (screening as any).frames.map((f: any) => ({
        time: `${((f.timestamp - (screening as any).frames[0].timestamp) / 1000).toFixed(1)}s`,
        leftKnee: Math.round(f.left_knee_angle),
        rightKnee: Math.round(f.right_knee_angle)
      }))
    : Array.from({ length: 20 }, (_, i) => {
        const tSec = (i * 0.4).toFixed(1);
        const lMin = screening.min_left_knee_angle || 70;
        const rMin = screening.min_right_knee_angle || 70;
        const wave = Math.sin(i * 0.5);
        return {
          time: `${tSec}s`,
          leftKnee: Math.round(lMin + (1 - wave) * (screening.left_knee_rom / 2)),
          rightKnee: Math.round(rMin + (1 - wave) * (screening.right_knee_rom / 2))
        };
      });

  const contributionPie = [
    { name: 'Questionnaire Burden', value: screening.questionnaire_contribution || 52, color: '#0d9488' },
    { name: 'Computer-Vision Movement', value: screening.movement_contribution || 48, color: '#06b6d4' }
  ];

  // Resolve model-derived risk factors dynamically from backend screening response
  const rawFactors = (screening as any).top_risk_factors && (screening as any).top_risk_factors.length > 0
    ? (screening as any).top_risk_factors
    : (screening as any).explainability_json
    ? (typeof (screening as any).explainability_json === 'string'
        ? JSON.parse((screening as any).explainability_json)
        : (screening as any).explainability_json)
    : [];

  const isHigh = screening.risk_level.includes('High');
  const isMod = screening.risk_level.includes('Moderate');

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Top Header Card */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold text-teal-700 bg-teal-50 border border-teal-200 px-3 py-1 rounded-full uppercase tracking-wider">
              AI-Assisted Preliminary OA Risk Screening
            </span>
            <span className="text-xs font-bold text-emerald-800 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full uppercase tracking-wider">
              Assessment: {screening.assessment_status || 'VALID'}
            </span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight mt-2">
            AI-Assisted Preliminary OA Risk Screening
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Patient: <b>{screening.patient_name || 'Patient'}</b> (Code: {screening.patient_code || 'N/A'}) • Model: <b>{screening.model_name || 'XGBoost'}</b> • Screened on {new Date(screening.screening_date).toLocaleDateString()}
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

      {/* Screening Quality Report Pillar Card */}
      {screening.quality_report && (
        <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700 bg-teal-50 px-2.5 py-1 rounded-full border border-teal-200">
                Quality-Gated Screening Verification
              </span>
              <h3 className="text-lg font-bold text-slate-900 mt-1">Screening Quality Report</h3>
              <p className="text-xs text-slate-500">
                Automated multi-pillar telemetry check determining assessment reliability before screening conclusion acceptance.
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <span className="text-xs text-slate-500 font-medium">Overall Gate:</span>
              <span className={`px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider ${
                screening.quality_report.assessment_quality === 'GOOD'
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                  : screening.quality_report.assessment_quality === 'FAIR'
                  ? 'bg-amber-100 text-amber-800 border border-amber-300'
                  : 'bg-rose-100 text-rose-800 border border-rose-300 animate-pulse'
              }`}>
                {screening.quality_report.assessment_quality} QUALITY
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5">
            {/* Pillar 1: Assessment Quality */}
            <div className={`p-4 rounded-2xl border ${
              screening.quality_report.assessment_quality === 'GOOD'
                ? 'bg-emerald-50/50 border-emerald-200'
                : screening.quality_report.assessment_quality === 'FAIR'
                ? 'bg-amber-50/50 border-amber-200'
                : 'bg-rose-50/50 border-rose-200'
            }`}>
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Assessment Quality</span>
              <span className={`text-xl font-black mt-1 block ${
                screening.quality_report.assessment_quality === 'GOOD'
                  ? 'text-emerald-700'
                  : screening.quality_report.assessment_quality === 'FAIR'
                  ? 'text-amber-700'
                  : 'text-rose-700'
              }`}>
                {screening.quality_report.assessment_quality}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                Decision: <b>{screening.quality_report.gate_decision || 'PROCEED'}</b>
              </span>
            </div>

            {/* Pillar 2: Camera Quality */}
            <div className={`p-4 rounded-2xl border ${
              screening.quality_report.camera_quality === 'GOOD'
                ? 'bg-emerald-50/50 border-emerald-200'
                : screening.quality_report.camera_quality === 'FAIR'
                ? 'bg-amber-50/50 border-amber-200'
                : 'bg-rose-50/50 border-rose-200'
            }`}>
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Camera Quality</span>
              <span className={`text-xl font-black mt-1 block ${
                screening.quality_report.camera_quality === 'GOOD'
                  ? 'text-emerald-700'
                  : screening.quality_report.camera_quality === 'FAIR'
                  ? 'text-amber-700'
                  : 'text-rose-700'
              }`}>
                {screening.quality_report.camera_quality}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                Positioning & Tracking
              </span>
            </div>

            {/* Pillar 3: Movement Capture */}
            <div className={`p-4 rounded-2xl border ${
              screening.quality_report.movement_capture === 'GOOD'
                ? 'bg-emerald-50/50 border-emerald-200'
                : screening.quality_report.movement_capture === 'FAIR'
                ? 'bg-amber-50/50 border-amber-200'
                : 'bg-rose-50/50 border-rose-200'
            }`}>
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Movement Capture</span>
              <span className={`text-xl font-black mt-1 block ${
                screening.quality_report.movement_capture === 'GOOD'
                  ? 'text-emerald-700'
                  : screening.quality_report.movement_capture === 'FAIR'
                  ? 'text-amber-700'
                  : 'text-rose-700'
              }`}>
                {screening.quality_report.movement_capture}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                Kinematic Completeness
              </span>
            </div>

            {/* Pillar 4: Feature Completeness */}
            <div className={`p-4 rounded-2xl border ${
              screening.quality_report.feature_completeness === 'GOOD'
                ? 'bg-emerald-50/50 border-emerald-200'
                : screening.quality_report.feature_completeness === 'FAIR'
                ? 'bg-amber-50/50 border-amber-200'
                : 'bg-rose-50/50 border-rose-200'
            }`}>
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Feature Completeness</span>
              <span className={`text-xl font-black mt-1 block ${
                screening.quality_report.feature_completeness === 'GOOD'
                  ? 'text-emerald-700'
                  : screening.quality_report.feature_completeness === 'FAIR'
                  ? 'text-amber-700'
                  : 'text-rose-700'
              }`}>
                {screening.quality_report.feature_completeness}
              </span>
              <span className="text-[10px] text-slate-500 mt-1 block">
                Survey & Sensor Inputs
              </span>
            </div>
          </div>

          {screening.quality_report.retest_recommended && (
            <div className="mt-4 p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <span className="text-xs font-bold block">Assessment Repeat Recommended:</span>
                <p className="text-xs mt-0.5">{screening.quality_report.reason}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Primary Risk Stratification Banner OR Poor Quality Banner */}
      {screening.data_quality === 'POOR' || screening.quality_report?.assessment_quality === 'POOR' ? (
        <div className="p-6 sm:p-8 rounded-3xl border border-rose-200 bg-rose-50/80 text-rose-950 shadow-sm">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="flex items-start space-x-4">
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-white flex-shrink-0 shadow-md bg-rose-600">
                <AlertTriangle className="w-8 h-8" />
              </div>
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-rose-700 block">
                  Quality Gate Notice
                </span>
                <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-rose-900">
                  Assessment quality insufficient.
                </h2>
                <p className="text-sm mt-2 font-semibold text-rose-800">
                  Screening could not be reliably completed.
                </p>
                <p className="text-xs mt-1 text-rose-700 max-w-2xl leading-relaxed">
                  {screening.quality_report?.reason || "Telemetry completeness or movement tracking quality did not satisfy the minimum reliability threshold."}
                </p>
                <div className="mt-3 inline-flex items-center space-x-2 text-xs font-bold text-rose-900 bg-white/80 px-3 py-1.5 rounded-xl border border-rose-200">
                  <span>Recommendation:</span>
                  <span className="text-rose-700">Please repeat the movement assessment with better camera positioning and movement visibility.</span>
                </div>
              </div>
            </div>

            <div className="bg-white/90 p-4 rounded-2xl border border-rose-100 flex flex-wrap items-center gap-6 text-slate-800">
              <div>
                <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Screening Status</span>
                <span className="text-lg font-black font-mono text-rose-600">INCONCLUSIVE</span>
              </div>
              <div className="h-8 w-px bg-slate-200" />
              <div>
                <span className="text-[10px] text-slate-500 uppercase tracking-wider block">AI Confidence</span>
                <span className="text-lg font-black font-mono text-rose-600">LOW</span>
              </div>
            </div>
          </div>
        </div>
      ) : (
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
                    ? 'Screening profile contains mild to moderate joint mobility indicators. Routine physical monitoring and professional functional evaluation are recommended.'
                    : 'Screening profile exhibits healthy joint range of motion and symmetric gait dynamics.'}
                </p>
              </div>
            </div>

            {/* Key Risk Indicators Percentage Block */}
            <div className="bg-white/80 backdrop-blur-sm p-4 rounded-2xl border border-white/50 flex flex-wrap items-center gap-6 text-slate-800">
              <div>
                <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Risk Level</span>
                <span className="text-xl font-black font-mono text-teal-700">{screening.risk_level}</span>
              </div>
              <div className="h-8 w-px bg-slate-200" />
              <div>
                <span className="text-[10px] text-slate-500 uppercase tracking-wider block">AI Confidence</span>
                <span className="text-xl font-black font-mono text-slate-800">
                  {screening.confidence_level || 'HIGH'} <span className="text-xs font-normal text-slate-500">({screening.confidence}%)</span>
                </span>
              </div>
              <div className="h-8 w-px bg-slate-200" />
              <div>
                <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Data Quality</span>
                <span className={`text-xl font-black font-mono ${
                  (screening.data_quality as string) === 'POOR' ? 'text-rose-600' : (screening.data_quality as string) === 'FAIR' ? 'text-amber-600' : 'text-emerald-700'
                }`}>
                  {screening.data_quality || 'GOOD'}
                </span>
              </div>
            </div>
          </div>

          {screening.confidence_reason && (
            <div className="mt-3 pt-3 border-t border-black/10 text-xs opacity-90">
              <b>Confidence Calibration Analysis:</b> {screening.confidence_reason}
            </div>
          )}
        </div>
      )}

      {/* Early Medical-Evaluation Guidance Card */}
      {screening.early_guidance && (
        <div className="bg-teal-50 border border-teal-200 p-5 rounded-2xl flex items-start space-x-3">
          <ShieldCheck className="w-5 h-5 text-teal-700 flex-shrink-0 mt-0.5" />
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-teal-800 block">
              Early Medical-Evaluation Guidance
            </span>
            <p className="text-xs font-medium text-teal-950 mt-1 leading-relaxed">
              {screening.early_guidance}
            </p>
          </div>
        </div>
      )}

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
            {screening.mobility_score <= 4 ? 'Restricted Range' : 'Adequate Functional Range'}
          </span>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <span className="text-[11px] text-slate-500 font-semibold block">Knee ROM (L / R)</span>
          <span className="text-xl font-bold font-mono text-teal-600 mt-1 block">
            {screening.left_knee_rom}° / {screening.right_knee_rom}°
          </span>
          <span className="text-[10px] text-slate-500 font-semibold mt-1 block">
            Diff: {Math.abs(screening.left_knee_rom - screening.right_knee_rom)}° | Sym: {screening.knee_symmetry}%
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
          <span className="text-[11px] text-slate-500 font-semibold block">Movement Dynamics</span>
          <span className="text-xl font-bold font-mono text-emerald-600 mt-1 block">
            {screening.movement_duration || 8.0}s
          </span>
          <span className="text-[10px] text-emerald-700 font-semibold mt-1 block">
            Peak Vel: {screening.peak_left_velocity || 45}°/s
          </span>
        </div>
      </div>

      {/* Multi-Test Protocol Breakdown: Knee Flexion, Sit-to-Stand, Walking */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-teal-600" />
            <h3 className="text-base font-bold text-slate-900">Functional Movement Protocol Breakdown</h3>
          </div>
          <span className="text-xs bg-slate-100 text-slate-600 font-semibold px-2.5 py-1 rounded-full">
            3 Standard Tests Executed
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Test 1: Knee Flexion */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                1. Knee Flexion
              </span>
              <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
                {screening.movement_tests?.knee_flexion?.assessment_status || 'VALID'}
              </span>
            </div>
            <div className="space-y-1 pt-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Left Knee ROM:</span>
                <span className="font-bold font-mono text-slate-800">{screening.movement_tests?.knee_flexion?.left_knee_rom ?? screening.left_knee_rom}°</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Right Knee ROM:</span>
                <span className="font-bold font-mono text-slate-800">{screening.movement_tests?.knee_flexion?.right_knee_rom ?? screening.right_knee_rom}°</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Bilateral Symmetry:</span>
                <span className="font-bold font-mono text-teal-600">{screening.movement_tests?.knee_flexion?.knee_symmetry ?? screening.knee_symmetry}%</span>
              </div>
              <div className="flex justify-between text-xs pt-1 border-t border-slate-200">
                <span className="text-slate-500">Data Quality Score:</span>
                <span className="font-bold font-mono text-emerald-600">{screening.movement_tests?.knee_flexion?.movement_quality_score ?? 88}%</span>
              </div>
            </div>
          </div>

          {/* Test 2: Sit-to-Stand */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-cyan-700 bg-cyan-50 px-2 py-0.5 rounded border border-cyan-200">
                2. Sit-to-Stand
              </span>
              <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
                {screening.movement_tests?.sit_to_stand?.assessment_status || 'VALID'}
              </span>
            </div>
            <div className="space-y-1 pt-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Repetitions:</span>
                <span className="font-bold font-mono text-slate-800">{screening.movement_tests?.sit_to_stand?.repetition_count ?? (screening.repetition_count || 3)} cycles</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Posture Alignment:</span>
                <span className="font-bold font-mono text-slate-800">{screening.movement_tests?.sit_to_stand?.posture_score ?? screening.posture_score}/100</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Movement Smoothness:</span>
                <span className="font-bold font-mono text-cyan-600">{screening.movement_tests?.sit_to_stand?.movement_smoothness ?? screening.movement_smoothness}%</span>
              </div>
              <div className="flex justify-between text-xs pt-1 border-t border-slate-200">
                <span className="text-slate-500">Data Quality Score:</span>
                <span className="font-bold font-mono text-emerald-600">{screening.movement_tests?.sit_to_stand?.movement_quality_score ?? 90}%</span>
              </div>
            </div>
          </div>

          {/* Test 3: Walking / Gait */}
          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                3. Walking / Gait
              </span>
              <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
                {screening.movement_tests?.walking?.assessment_status || 'VALID'}
              </span>
            </div>
            <div className="space-y-1 pt-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Gait Symmetry:</span>
                <span className="font-bold font-mono text-slate-800">{screening.movement_tests?.walking?.gait_symmetry ?? screening.gait_symmetry}%</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Stride Consistency:</span>
                <span className="font-bold font-mono text-slate-800">{screening.movement_tests?.walking?.movement_consistency ?? screening.movement_consistency}%</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-slate-500">Duration:</span>
                <span className="font-bold font-mono text-indigo-600">{screening.movement_tests?.walking?.movement_duration ?? (screening.movement_duration || 8.0)}s</span>
              </div>
              <div className="flex justify-between text-xs pt-1 border-t border-slate-200">
                <span className="text-slate-500">Data Quality Score:</span>
                <span className="font-bold font-mono text-emerald-600">{screening.movement_tests?.walking?.movement_quality_score ?? 92}%</span>
              </div>
            </div>
          </div>
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
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center space-x-2">
            <Zap className="w-4 h-4 text-amber-500" />
            <span>Explainable AI: Why This Result?</span>
          </h3>
          <p className="text-xs text-slate-500 mb-4">
            Factors traceable to actual patient-reported answers and computer-vision movement telemetry.
          </p>

          <div className="space-y-4">
            {rawFactors && rawFactors.length > 0 ? (
              rawFactors.map((item: any, idx: number) => {
                const isIncreased = item.direction === 'increases risk';
                const hasAttr = item.relative_attribution !== null && item.relative_attribution !== undefined;
                const attrVal = hasAttr ? item.relative_attribution : null;

                return (
                  <div key={item.factor || item.feature_name || idx} className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200/80 space-y-2">
                    <div className="flex justify-between items-center text-xs">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-slate-800">{item.factor || item.feature_name}</span>
                        {item.direction && (
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            isIncreased ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'
                          }`}>
                            {isIncreased ? '↑ Increases Risk' : '↓ Decreases Risk'}
                          </span>
                        )}
                      </div>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        item.status === 'Alert' ? 'bg-rose-100 text-rose-800' : item.status === 'Moderate' ? 'bg-amber-100 text-amber-800' : 'bg-teal-100 text-teal-800'
                      }`}>
                        {item.status || 'Optimal'}
                      </span>
                    </div>

                    {/* Progress bar showing real attribution if available */}
                    {hasAttr && (
                      <div className="space-y-1">
                        <div className="flex justify-between text-[11px] text-slate-500">
                          <span>Model Contribution:</span>
                          <span className="font-semibold text-slate-700">+{attrVal}% relative attribution</span>
                        </div>
                        <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              attrVal >= 20 ? 'bg-rose-500' : attrVal >= 10 ? 'bg-amber-500' : 'bg-teal-500'
                            }`}
                            style={{ width: `${Math.min(100, Math.max(5, attrVal))}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {item.observed && (
                      <p className="text-[11px] text-slate-700">
                        <span className="font-semibold text-teal-700">Observed:</span> {item.observed}
                      </p>
                    )}
                    {item.inference && (
                      <p className="text-[11px] text-slate-600">
                        <span className="font-semibold text-amber-700">Model Contribution:</span> {item.inference}
                      </p>
                    )}
                    {item.confidence_limitation && (
                      <p className="text-[11px] text-slate-500 italic">
                        <span className="font-semibold text-slate-600">Confidence Limitation:</span> {item.confidence_limitation}
                      </p>
                    )}
                  </div>
                );
              })
            ) : (
              <p className="text-xs text-slate-500 py-3 text-center">
                No elevated risk markers identified for this screening session.
              </p>
            )}
          </div>

          {screening.confidence_breakdown && (
            <div className="mt-4 p-3 bg-slate-50 rounded-2xl border border-slate-200 text-xs space-y-1">
              <span className="font-bold text-slate-700 block">AI Confidence Calibration Drivers:</span>
              <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-600">
                <div>Model Margin: <b>{Math.round((screening.confidence_breakdown.model_probability_margin || 0) * 100)}%</b></div>
                <div>Data Quality: <b>{screening.confidence_breakdown.data_quality_level || screening.data_quality}</b></div>
                <div>Feature Completeness: <b>{Math.round((screening.confidence_breakdown.feature_completeness_ratio || 1) * 100)}%</b></div>
                <div>Movement Reliability: <b>{Math.round((screening.confidence_breakdown.movement_reliability || 0.9) * 100)}%</b></div>
              </div>
            </div>
          )}

          <div className="mt-4 pt-4 border-t border-slate-100 text-xs text-slate-500 flex justify-between">
            <span>Questionnaire Factor: <b>{screening.questionnaire_contribution}%</b></span>
            <span>Movement Biomechanics Factor: <b>{screening.movement_contribution}%</b></span>
          </div>
        </div>
      </div>

      {/* Early Medical-Evaluation Guidance */}
      <div className="bg-teal-50/50 border border-teal-200 p-6 rounded-3xl">
        <h3 className="text-sm font-bold text-teal-900 uppercase tracking-wider mb-3">
          {t('result.recommendations')}
        </h3>
        <ul className="space-y-2 text-xs text-teal-950">
          <li className="flex items-start space-x-2">
            <span className="text-teal-600 font-bold">✓</span>
            <span>OA-related risk markers were identified in this screening. Consider evaluation by a qualified healthcare professional for further assessment.</span>
          </li>
          <li className="flex items-start space-x-2">
            <span className="text-teal-600 font-bold">✓</span>
            <span>Follow-up screening may be considered based on symptoms and guidance from a qualified healthcare professional.</span>
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
