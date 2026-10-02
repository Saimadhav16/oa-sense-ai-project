import React, { useState, useEffect } from 'react';
import { Users, PlusCircle, Search, ArrowRight, UserPlus } from 'lucide-react';
import { Patient } from '../types';
import { api } from '../services/api';
import { useTranslation } from '../utils/i18n';

interface PatientsListPageProps {
  onSelectPatient: (id: number) => void;
  onRegisterPatient: () => void;
  onStartScreening: (p: Patient) => void;
}

export const PatientsListPage: React.FC<PatientsListPageProps> = ({
  onSelectPatient,
  onRegisterPatient,
  onStartScreening
}) => {
  const { t } = useTranslation();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [search, setSearch] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async () => {
    setLoading(true);
    try {
      const data = await api.getPatients(search);
      setPatients(data);
    } catch (e) {
      console.warn('Error loading patients:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadPatients();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Patient Directory</h1>
          <p className="text-xs text-slate-500 mt-1">Cohort records, clinical risk factors, and screening links</p>
        </div>

        <button
          onClick={onRegisterPatient}
          className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs shadow-md shadow-teal-600/20 flex items-center space-x-1.5 transition"
        >
          <UserPlus className="w-4 h-4" />
          <span>{t('patient.register')}</span>
        </button>
      </div>

      {/* Search Input Bar */}
      <form onSubmit={handleSearchSubmit} className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name, patient code, or phone..."
          className="w-full pl-10 pr-4 py-2.5 rounded-2xl border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white shadow-xs"
        />
      </form>

      {/* Patient Cards List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {patients.map((p) => (
          <div
            key={p.id}
            className="bg-white p-5 rounded-2xl border border-slate-200 hover:border-teal-300 shadow-xs transition flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="font-mono text-[11px] font-bold text-teal-700 bg-teal-50 border border-teal-200 px-2.5 py-0.5 rounded-md">
                  {p.patient_code}
                </span>
                <span className="text-xs text-slate-400">{p.gender}, {p.age}y</span>
              </div>
              <h3 className="text-base font-bold text-slate-900">{p.name}</h3>
              <p className="text-xs text-slate-500 mt-0.5">{p.occupation || 'Laborer / Worker'} • {p.location || 'Rural Site'}</p>
            </div>

            <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between">
              <button
                onClick={() => onSelectPatient(p.id)}
                className="text-xs font-semibold text-slate-600 hover:text-slate-900"
              >
                View History
              </button>
              <button
                onClick={() => onStartScreening(p)}
                className="px-3 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold transition flex items-center space-x-1"
              >
                <span>Screen</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
