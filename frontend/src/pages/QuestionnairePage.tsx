import React, { useState } from 'react';
import { ClipboardList, ArrowRight, ArrowLeft, Info } from 'lucide-react';
import { QuestionnaireData, Patient } from '../types';
import { useTranslation } from '../utils/i18n';

interface QuestionnairePageProps {
  patient: Patient;
  onComplete: (data: QuestionnaireData) => void;
  onBack: () => void;
}

const LIKERT_OPTIONS = [
  { val: 0, labelKey: 'q.optNever' },
  { val: 1, labelKey: 'q.optRarely' },
  { val: 2, labelKey: 'q.optSometimes' },
  { val: 3, labelKey: 'q.optOften' },
  { val: 4, labelKey: 'q.optAlways' }
];

export const QuestionnairePage: React.FC<QuestionnairePageProps> = ({
  patient,
  onComplete,
  onBack
}) => {
  const { t } = useTranslation();

  const [responses, setResponses] = useState<QuestionnaireData>({
    knee_pain: 2,
    joint_stiffness: 2,
    walking_difficulty: 1,
    stair_difficulty: 2,
    standing_difficulty: 1,
    knee_bending_difficulty: 2,
    pain_increase_activity: 2,
    pain_scale: 4.5,
    mobility_scale: 6.5
  });

  const handleLikert = (key: keyof QuestionnaireData, val: number) => {
    setResponses(prev => ({ ...prev, [key]: val }));
  };

  const questions: Array<{ key: keyof QuestionnaireData; labelKey: string }> = [
    { key: 'knee_pain', labelKey: 'q.q1' },
    { key: 'joint_stiffness', labelKey: 'q.q2' },
    { key: 'walking_difficulty', labelKey: 'q.q3' },
    { key: 'stair_difficulty', labelKey: 'q.q4' },
    { key: 'standing_difficulty', labelKey: 'q.q5' },
    { key: 'knee_bending_difficulty', labelKey: 'q.q6' },
    { key: 'pain_increase_activity', labelKey: 'q.q7' }
  ];

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 sm:p-10 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between pb-6 border-b border-slate-100">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-2xl bg-teal-600 text-white flex items-center justify-center shadow-md shadow-teal-600/20">
              <ClipboardList className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">{t('q.title')}</h1>
              <p className="text-xs text-slate-500">
                Patient: <b>{patient.name}</b> ({patient.patient_code}, {patient.age}y)
              </p>
            </div>
          </div>
          <span className="text-xs bg-teal-50 text-teal-700 font-bold px-3 py-1 rounded-full border border-teal-200">
            Step 1 of 2
          </span>
        </div>

        {/* Informative Note */}
        <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 text-xs text-slate-600 flex items-start space-x-2.5">
          <Info className="w-4 h-4 text-teal-600 flex-shrink-0 mt-0.5" />
          <span>
            These responses provide functional symptom metrics. Responses alone do <b>not</b> constitute an OA diagnosis, but help stratify functional risk when combined with movement tracking.
          </span>
        </div>

        {/* Likert Scale Questions */}
        <div className="space-y-6">
          {questions.map((q, qIndex) => (
            <div key={q.key} className="bg-slate-50/50 p-4 rounded-2xl border border-slate-100 space-y-3">
              <h3 className="text-xs font-bold text-slate-800 leading-snug">
                {t(q.labelKey)}
              </h3>
              <div className="grid grid-cols-5 gap-2">
                {LIKERT_OPTIONS.map((opt) => {
                  const isSelected = responses[q.key] === opt.val;
                  return (
                    <button
                      key={opt.val}
                      type="button"
                      onClick={() => handleLikert(q.key, opt.val)}
                      className={`py-2 px-1 text-center rounded-xl text-xs font-semibold border transition ${
                        isSelected
                          ? 'bg-teal-600 border-teal-600 text-white shadow-xs'
                          : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-100'
                      }`}
                    >
                      <span className="block">{t(opt.labelKey)}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Sliders: Pain and Mobility Scales */}
        <div className="space-y-6 pt-4 border-t border-slate-100">
          {/* Pain Scale (0 - 10) */}
          <div className="bg-rose-50/40 p-5 rounded-2xl border border-rose-100">
            <div className="flex justify-between items-center mb-2">
              <label className="text-xs font-bold text-slate-800">
                {t('q.q8')}
              </label>
              <span className="px-3 py-1 rounded-lg bg-rose-600 text-white font-mono font-bold text-sm">
                {responses.pain_scale} / 10
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="10"
              step="0.5"
              value={responses.pain_scale}
              onChange={(e) => setResponses({ ...responses, pain_scale: parseFloat(e.target.value) })}
              className="w-full accent-rose-600 h-2 bg-slate-200 rounded-lg cursor-pointer"
            />
            <div className="flex justify-between text-[11px] text-slate-400 font-medium mt-1">
              <span>0 (No Pain)</span>
              <span>5 (Moderate Pain)</span>
              <span>10 (Severe Pain)</span>
            </div>
          </div>

          {/* Mobility Scale (0 - 10) */}
          <div className="bg-teal-50/40 p-5 rounded-2xl border border-teal-100">
            <div className="flex justify-between items-center mb-2">
              <label className="text-xs font-bold text-slate-800">
                {t('q.q9')}
              </label>
              <span className="px-3 py-1 rounded-lg bg-teal-600 text-white font-mono font-bold text-sm">
                {responses.mobility_scale} / 10
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="10"
              step="0.5"
              value={responses.mobility_scale}
              onChange={(e) => setResponses({ ...responses, mobility_scale: parseFloat(e.target.value) })}
              className="w-full accent-teal-600 h-2 bg-slate-200 rounded-lg cursor-pointer"
            />
            <div className="flex justify-between text-[11px] text-slate-400 font-medium mt-1">
              <span>0 (Immobile)</span>
              <span>5 (Moderate Limitations)</span>
              <span>10 (Full Unrestricted Mobility)</span>
            </div>
          </div>
        </div>

        {/* Progression Controls */}
        <div className="flex items-center justify-between pt-6 border-t border-slate-100">
          <button
            type="button"
            onClick={onBack}
            className="px-4 py-2.5 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 text-xs font-semibold flex items-center space-x-1.5"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </button>

          <button
            type="button"
            onClick={() => onComplete(responses)}
            className="px-6 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold shadow-md shadow-teal-600/20 flex items-center space-x-2"
          >
            <span>{t('q.next')}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
