import React, { useState } from 'react';
import { CameraMovementTracker } from '../components/CameraMovementTracker';
import { Patient, QuestionnaireData, MovementSummary, ScreeningRecord } from '../types';
import { api } from '../services/api';
import { Loader2, ArrowLeft } from 'lucide-react';

interface MovementScreeningPageProps {
  patient: Patient;
  questionnaire: QuestionnaireData;
  onScreeningFinished: (record: ScreeningRecord) => void;
  onBack: () => void;
}

export const MovementScreeningPage: React.FC<MovementScreeningPageProps> = ({
  patient,
  questionnaire,
  onScreeningFinished,
  onBack
}) => {
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleMovementComplete = async (summary: MovementSummary) => {
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const record = await api.submitScreening({
        patient_id: patient.id,
        questionnaire,
        movement: summary,
        notes: `Screening test completed for ${patient.name}`
      });
      onScreeningFinished(record);
    } catch (err: any) {
      if (err.message === 'OFFLINE_SAVED') {
        // Fallback simulated local record for immediate UI feedback in offline mode
        const localRecord: ScreeningRecord = {
          id: Date.now(),
          patient_id: patient.id,
          patient_name: patient.name,
          patient_code: patient.patient_code,
          screening_date: new Date().toISOString(),
          pain_score: questionnaire.pain_scale,
          stiffness_score: questionnaire.joint_stiffness,
          mobility_score: questionnaire.mobility_scale,
          left_knee_rom: summary.left_knee_rom,
          right_knee_rom: summary.right_knee_rom,
          knee_symmetry: summary.knee_symmetry,
          average_knee_angle: summary.average_knee_angle,
          gait_symmetry: summary.gait_symmetry,
          movement_consistency: summary.movement_consistency,
          posture_score: summary.posture_score,
          movement_smoothness: summary.movement_smoothness,
          risk_level: summary.left_knee_rom < 95 || questionnaire.pain_scale >= 6 ? 'High Risk' : 'Moderate Risk',
          risk_probability: 72.5,
          confidence: 89.0,
          questionnaire_contribution: 54.0,
          movement_contribution: 46.0,
          sync_status: 'pending_sync',
          model_version: '1.0.0-demo',
          created_at: new Date().toISOString()
        };
        onScreeningFinished(localRecord);
      } else {
        setSubmitError(err.message || 'Error processing screening analysis.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="px-3.5 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 flex items-center space-x-1.5"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Questionnaire</span>
        </button>

        <div className="text-right">
          <span className="text-xs font-bold text-slate-800">{patient.name}</span>
          <span className="text-xs text-slate-400 block">{patient.patient_code} | {patient.age}y</span>
        </div>
      </div>

      {submitError && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium">
          {submitError}
        </div>
      )}

      {isSubmitting ? (
        <div className="bg-white p-12 rounded-3xl border border-slate-200 text-center space-y-4 shadow-sm">
          <Loader2 className="w-10 h-10 text-teal-600 animate-spin mx-auto" />
          <h2 className="text-lg font-bold text-slate-900">Executing Machine Learning Risk Pipeline...</h2>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Combining biomechanical computer-vision landmarks with functional questionnaire metrics to generate explainable risk stratification.
          </p>
        </div>
      ) : (
        <CameraMovementTracker
          patientName={patient.name}
          onComplete={handleMovementComplete}
        />
      )}
    </div>
  );
};
