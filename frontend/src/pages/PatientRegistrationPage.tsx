import React, { useState } from 'react';
import { UserPlus, ArrowRight, Save, CheckSquare, Square, Shield } from 'lucide-react';
import { Patient } from '../types';
import { api } from '../services/api';
import { useTranslation } from '../utils/i18n';

interface PatientRegistrationPageProps {
  onPatientSaved: (patient: Patient, proceedToScreening: boolean) => void;
  onCancel: () => void;
}

export const PatientRegistrationPage: React.FC<PatientRegistrationPageProps> = ({
  onPatientSaved,
  onCancel
}) => {
  const { t } = useTranslation();

  const [formData, setFormData] = useState({
    name: '',
    age: 52,
    gender: 'Female',
    phone: '',
    location: '',
    occupation: '',
    activity_level: 'Moderate',
    joint_injury: 0,
    family_history: 0,
    demanding_work: 0,
    walking_difficulty: 0,
    stair_difficulty: 0,
    morning_stiffness: 0
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleFactor = (key: keyof typeof formData) => {
    setFormData(prev => ({
      ...prev,
      [key]: prev[key] === 1 ? 0 : 1
    }));
  };

  const handleSubmit = async (proceedToScreening: boolean) => {
    if (!formData.name.trim()) {
      setError('Patient name is required.');
      return;
    }
    setError(null);
    setLoading(true);

    try {
      const newPatient = await api.createPatient(formData);
      onPatientSaved(newPatient, proceedToScreening);
    } catch (err: any) {
      setError(err.message || 'Failed to register patient');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 sm:p-10">
        {/* Header */}
        <div className="flex items-center space-x-3 mb-6 pb-6 border-b border-slate-100">
          <div className="w-12 h-12 rounded-2xl bg-teal-600 text-white flex items-center justify-center shadow-md shadow-teal-600/20">
            <UserPlus className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">{t('patient.register')}</h1>
            <p className="text-xs text-slate-500">{t('patient.subtitle')}</p>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
            {error}
          </div>
        )}

        {/* Demographics Section */}
        <div className="space-y-5">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">1. Demographic Information</h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="sm:col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1">{t('patient.fullName')} *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g. Maya Patel"
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">{t('patient.ageLabel')} *</label>
              <input
                type="number"
                min={18}
                max={100}
                required
                value={formData.age}
                onChange={(e) => setFormData({ ...formData, age: parseInt(e.target.value) || 50 })}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">{t('patient.gender')} *</label>
              <select
                value={formData.gender}
                onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
              >
                <option value="Female">{t('patient.female')}</option>
                <option value="Male">{t('patient.male')}</option>
                <option value="Other">{t('patient.other')}</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">{t('patient.phone')}</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="+91 98765 43210"
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">{t('patient.location')}</label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                placeholder="District / Health Camp Site"
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">{t('patient.occupation')}</label>
              <input
                type="text"
                value={formData.occupation}
                onChange={(e) => setFormData({ ...formData, occupation: e.target.value })}
                placeholder="e.g. Farmer, Weaver, Teacher"
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">{t('patient.activityLevel')}</label>
              <select
                value={formData.activity_level}
                onChange={(e) => setFormData({ ...formData, activity_level: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
              >
                <option value="Sedentary">{t('patient.activitySedentary')}</option>
                <option value="Light">{t('patient.activityLight')}</option>
                <option value="Moderate">{t('patient.activityModerate')}</option>
                <option value="High">{t('patient.activityHigh')}</option>
              </select>
            </div>
          </div>
        </div>

        {/* Risk Factors Checklist */}
        <div className="mt-8 pt-6 border-t border-slate-100 space-y-4">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400">2. {t('patient.riskFactors')}</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              { key: 'joint_injury', label: t('patient.injury') },
              { key: 'family_history', label: t('patient.family') },
              { key: 'demanding_work', label: t('patient.demanding') },
              { key: 'walking_difficulty', label: t('patient.diffWalk') },
              { key: 'stair_difficulty', label: t('patient.diffStair') },
              { key: 'morning_stiffness', label: t('patient.stiffness') }
            ].map(item => {
              const isChecked = (formData as any)[item.key] === 1;
              return (
                <div
                  key={item.key}
                  onClick={() => toggleFactor(item.key as any)}
                  className={`p-3 rounded-xl border cursor-pointer flex items-center space-x-3 transition ${
                    isChecked
                      ? 'bg-teal-50 border-teal-300 text-teal-900 font-semibold'
                      : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                  }`}
                >
                  {isChecked ? (
                    <CheckSquare className="w-4 h-4 text-teal-600 flex-shrink-0" />
                  ) : (
                    <Square className="w-4 h-4 text-slate-400 flex-shrink-0" />
                  )}
                  <span className="text-xs">{item.label}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Buttons */}
        <div className="mt-8 pt-6 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 text-xs font-semibold"
          >
            Cancel
          </button>

          <div className="flex items-center space-x-3 w-full sm:w-auto justify-end">
            <button
              type="button"
              disabled={loading}
              onClick={() => handleSubmit(false)}
              className="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center justify-center space-x-1.5"
            >
              <Save className="w-4 h-4 text-slate-500" />
              <span>{t('patient.saveOnly')}</span>
            </button>

            <button
              type="button"
              disabled={loading}
              onClick={() => handleSubmit(true)}
              className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-md shadow-teal-600/20 flex items-center justify-center space-x-2"
            >
              <span>{t('patient.saveAndStart')}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
