import React, { useState, useEffect } from 'react';
import {
  Users,
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  PlusCircle,
  Search,
  ArrowRight,
  TrendingUp,
  Filter
} from 'lucide-react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { DashboardStats, Patient, RiskLevel } from '../types';
import { api } from '../services/api';
import { useTranslation } from '../utils/i18n';

interface DashboardPageProps {
  onStartNewScreening: () => void;
  onSelectPatient: (patientId: number) => void;
  onRegisterPatient: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onStartNewScreening,
  onSelectPatient,
  onRegisterPatient
}) => {
  const { t } = useTranslation();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [riskFilter, setRiskFilter] = useState<string>('all');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadDashboardData();
  }, [riskFilter]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [statsData, patientsData] = await Promise.all([
        api.getDashboardStats(),
        api.getPatients(searchQuery, riskFilter)
      ]);
      setStats(statsData);
      setPatients(patientsData);
    } catch (err) {
      console.warn('Error loading dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadDashboardData();
  };

  const pieData = [
    { name: 'Low Risk', value: stats?.risk_distribution['Low Risk'] || 0, color: '#10b981' },
    { name: 'Moderate Risk', value: stats?.risk_distribution['Moderate Risk'] || 0, color: '#f59e0b' },
    { name: 'High Risk', value: stats?.risk_distribution['High Risk'] || 0, color: '#ef4444' }
  ];

  const getRiskBadge = (risk?: RiskLevel) => {
    if (!risk) return <span className="text-slate-400 text-xs">Pending</span>;
    if (risk.includes('High')) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-200">
          <AlertTriangle className="w-3 h-3 mr-1" />
          {risk}
        </span>
      );
    }
    if (risk.includes('Moderate')) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200">
          <Clock className="w-3 h-3 mr-1" />
          {risk}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
        <CheckCircle className="w-3 h-3 mr-1" />
        {risk}
      </span>
    );
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">{t('dashboard.title')}</h1>
          <p className="text-sm text-slate-500 mt-1">{t('dashboard.subtitle')}</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={onRegisterPatient}
            className="px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-sm transition"
          >
            {t('patient.register')}
          </button>
          <button
            onClick={onStartNewScreening}
            className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-sm shadow-md shadow-teal-600/20 flex items-center space-x-2 transition"
          >
            <PlusCircle className="w-4 h-4" />
            <span>{t('dashboard.startScreening')}</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">{t('dashboard.totalPatients')}</span>
            <Users className="w-4 h-4 text-slate-400" />
          </div>
          <span className="text-2xl font-black text-slate-900">{stats?.total_patients ?? 0}</span>
          <span className="block text-[11px] text-teal-600 font-medium mt-1">Registered in cohort</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">{t('dashboard.screeningsToday')}</span>
            <Activity className="w-4 h-4 text-teal-600" />
          </div>
          <span className="text-2xl font-black text-teal-600">{stats?.screenings_today ?? 0}</span>
          <span className="block text-[11px] text-slate-400 mt-1">Sessions evaluated</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-rose-200 shadow-xs bg-gradient-to-br from-rose-50/40 to-white">
          <div className="flex items-center justify-between text-rose-600 mb-2">
            <span className="text-xs font-semibold">{t('dashboard.highRisk')}</span>
            <AlertTriangle className="w-4 h-4 text-rose-600" />
          </div>
          <span className="text-2xl font-black text-rose-600">{stats?.high_risk_cases ?? 0}</span>
          <span className="block text-[11px] text-rose-500 font-medium mt-1">Clinical follow-up req.</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-amber-200 shadow-xs bg-gradient-to-br from-amber-50/40 to-white">
          <div className="flex items-center justify-between text-amber-600 mb-2">
            <span className="text-xs font-semibold">{t('dashboard.modRisk')}</span>
            <Clock className="w-4 h-4 text-amber-600" />
          </div>
          <span className="text-2xl font-black text-amber-600">{stats?.moderate_risk_cases ?? 0}</span>
          <span className="block text-[11px] text-amber-500 font-medium mt-1">Routine monitoring</span>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-emerald-200 shadow-xs bg-gradient-to-br from-emerald-50/40 to-white col-span-2 lg:col-span-1">
          <div className="flex items-center justify-between text-emerald-600 mb-2">
            <span className="text-xs font-semibold">{t('dashboard.lowRisk')}</span>
            <CheckCircle className="w-4 h-4 text-emerald-600" />
          </div>
          <span className="text-2xl font-black text-emerald-600">{stats?.low_risk_cases ?? 0}</span>
          <span className="block text-[11px] text-emerald-500 font-medium mt-1">Healthy joint motility</span>
        </div>
      </div>

      {/* Analytics & Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution Donut */}
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
          <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4 flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-teal-600" />
            <span>{t('dashboard.riskDistribution')}</span>
          </h2>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-around text-xs mt-2 pt-2 border-t border-slate-100">
            {pieData.map(item => (
              <div key={item.name} className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-slate-600 font-medium">{item.name}: <b>{item.value}</b></span>
              </div>
            ))}
          </div>
        </div>

        {/* Screening Activity Feed */}
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs lg:col-span-2">
          <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4">
            Recent Screening Sessions
          </h2>
          {stats?.recent_activity && stats.recent_activity.length > 0 ? (
            <div className="space-y-3">
              {stats.recent_activity.slice(0, 4).map((act) => (
                <div
                  key={act.screening_id}
                  onClick={() => onSelectPatient(act.patient_id)}
                  className="p-3.5 rounded-xl border border-slate-100 bg-slate-50/70 hover:bg-teal-50/50 hover:border-teal-200 cursor-pointer flex items-center justify-between transition"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-9 h-9 rounded-lg bg-teal-100 text-teal-800 font-bold flex items-center justify-center text-xs">
                      {act.patient_name.charAt(0)}
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-bold text-slate-900">{act.patient_name}</span>
                        <span className="text-xs font-mono text-slate-400">({act.patient_code})</span>
                      </div>
                      <span className="text-xs text-slate-500">
                        Pain: {act.pain_score}/10 | Symmetry: {act.knee_symmetry}%
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    {getRiskBadge(act.risk_level)}
                    <ArrowRight className="w-4 h-4 text-slate-400" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-xs text-slate-400">
              No recent screening activity recorded yet.
            </div>
          )}
        </div>
      </div>

      {/* Patient Cohort Management Table */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-6 border-b border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-slate-900">{t('dashboard.recentPatients')}</h2>
            <p className="text-xs text-slate-500">Screening queue and risk indicator directory</p>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3 w-full md:w-auto">
            {/* Search Input */}
            <form onSubmit={handleSearch} className="relative w-full sm:w-64">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search patient or ID..."
                className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </form>

            {/* Risk Filters */}
            <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-xl text-xs w-full sm:w-auto justify-center">
              {['all', 'high', 'moderate', 'low'].map((f) => (
                <button
                  key={f}
                  onClick={() => setRiskFilter(f)}
                  className={`px-2.5 py-1 rounded-lg capitalize font-semibold transition ${
                    riskFilter === f ? 'bg-white text-teal-800 shadow-xs' : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Table View */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                <th className="py-3 px-6">{t('dashboard.patientId')}</th>
                <th className="py-3 px-6">{t('dashboard.name')}</th>
                <th className="py-3 px-6">{t('dashboard.age')}</th>
                <th className="py-3 px-6">Location</th>
                <th className="py-3 px-6">{t('dashboard.riskLevel')}</th>
                <th className="py-3 px-6 text-right">{t('dashboard.action')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {patients.length > 0 ? (
                patients.map((p) => (
                  <tr key={p.id} className="hover:bg-teal-50/40 transition">
                    <td className="py-3.5 px-6 font-mono text-xs font-semibold text-slate-700">
                      {p.patient_code}
                    </td>
                    <td className="py-3.5 px-6 font-semibold text-slate-900">
                      {p.name}
                    </td>
                    <td className="py-3.5 px-6 text-slate-600 text-xs">
                      {p.age} yrs ({p.gender})
                    </td>
                    <td className="py-3.5 px-6 text-slate-500 text-xs">
                      {p.location || 'Rural Centre'}
                    </td>
                    <td className="py-3.5 px-6">
                      {getRiskBadge(p.last_screening_risk)}
                    </td>
                    <td className="py-3.5 px-6 text-right space-x-2">
                      <button
                        onClick={() => onSelectPatient(p.id)}
                        className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold transition"
                      >
                        {t('dashboard.view')}
                      </button>
                      <button
                        onClick={() => {
                          onSelectPatient(p.id);
                          onStartNewScreening();
                        }}
                        className="px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold transition"
                      >
                        {t('dashboard.screen')}
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-400 text-xs">
                    No patients match the search or filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
