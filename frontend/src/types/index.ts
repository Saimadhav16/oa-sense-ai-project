export type RiskLevel = 'Low Risk' | 'Moderate Risk' | 'High Risk';

export interface User {
  id: number;
  name: string;
  email: string;
  role: string;
}

export interface Patient {
  id: number;
  patient_code: string;
  name: string;
  age: number;
  gender: string;
  phone?: string;
  location?: string;
  occupation?: string;
  activity_level: string;
  joint_injury: number;
  family_history: number;
  demanding_work: number;
  walking_difficulty: number;
  stair_difficulty: number;
  morning_stiffness: number;
  created_at: string;
  last_screening_risk?: RiskLevel;
  last_screening_date?: string;
}

export interface QuestionnaireData {
  knee_pain: number;
  joint_stiffness: number;
  walking_difficulty: number;
  stair_difficulty: number;
  standing_difficulty: number;
  knee_bending_difficulty: number;
  pain_increase_activity: number;
  pain_scale: number;
  mobility_scale: number;
}

export interface MovementFrameData {
  timestamp: number;
  left_knee_angle: number;
  right_knee_angle: number;
  hip_angle?: number;
  posture_value?: number;
}

export interface MovementSummary {
  left_knee_rom: number;
  right_knee_rom: number;
  knee_symmetry: number;
  average_knee_angle: number;
  gait_symmetry: number;
  movement_consistency: number;
  posture_score: number;
  hip_movement: number;
  ankle_movement: number;
  movement_smoothness: number;
  frames?: MovementFrameData[];
}

export interface RiskFactorItem {
  factor: string;
  importance: number;
  status: 'Optimal' | 'Moderate' | 'Alert' | string;
  detail: string;
}

export interface PredictionResult {
  risk_level: RiskLevel;
  risk_probability: number;
  confidence: number;
  questionnaire_contribution: number;
  movement_contribution: number;
  movement_indicator: 'Low' | 'Moderate' | 'High' | string;
  pain_mobility_indicator: 'Low' | 'Moderate' | 'High' | string;
  top_risk_factors: RiskFactorItem[];
  recommendations: string[];
  disclaimer: string;
  model_version: string;
}

export interface ScreeningRecord {
  id: number;
  patient_id: number;
  patient_name?: string;
  patient_code?: string;
  screening_date: string;
  pain_score: number;
  stiffness_score: number;
  mobility_score: number;
  left_knee_rom: number;
  right_knee_rom: number;
  knee_symmetry: number;
  average_knee_angle: number;
  gait_symmetry: number;
  movement_consistency: number;
  posture_score: number;
  movement_smoothness: number;
  risk_level: RiskLevel;
  risk_probability: number;
  confidence: number;
  questionnaire_contribution: number;
  movement_contribution: number;
  notes?: string;
  sync_status: 'synced' | 'pending_sync' | 'sync_failed';
  model_version: string;
  created_at: string;
  report_id?: number;
}

export interface DashboardStats {
  total_patients: number;
  screenings_today: number;
  high_risk_cases: number;
  moderate_risk_cases: number;
  low_risk_cases: number;
  risk_distribution: {
    'Low Risk': number;
    'Moderate Risk': number;
    'High Risk': number;
  };
  recent_activity: Array<{
    screening_id: number;
    patient_id: number;
    patient_name: string;
    patient_code: string;
    age: number;
    risk_level: RiskLevel;
    risk_probability: number;
    pain_score: number;
    knee_symmetry: number;
    screening_date: string;
  }>;
}
