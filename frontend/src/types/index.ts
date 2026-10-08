export type RiskLevel = 'Low Risk' | 'Moderate Risk' | 'High Risk';
export type ConfidenceCategory = 'HIGH' | 'MEDIUM' | 'LOW';
export type DataQualityCategory = 'GOOD' | 'FAIR' | 'POOR';
export type TrajectoryStatus = 'Stable' | 'Improving' | 'Worsening' | 'Inconclusive';

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
  doctor_notes?: string;
  referral_info?: string;
  follow_up_instructions?: string;
  created_at: string;
  updated_at?: string;
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
  frame_valid?: boolean;
  phase?: 'flexion' | 'extension' | 'hold' | 'stationary' | string;
  movement_type?: 'KNEE_FLEXION' | 'SIT_TO_STAND' | 'WALKING' | string;
}

export interface MovementTestResult {
  test_type: 'KNEE_FLEXION' | 'SIT_TO_STAND' | 'WALKING';
  assessment_status: 'VALID' | 'REPEAT_REQUIRED' | 'INSUFFICIENT_DATA';
  movement_quality_score: number;
  landmark_quality_score: number;
  valid_frame_ratio: number;
  valid_frames_count: number;
  total_frames_count: number;
  movement_duration: number;
  validation_message?: string;
  left_knee_rom?: number;
  right_knee_rom?: number;
  knee_symmetry?: number;
  average_knee_angle?: number;
  repetition_count?: number;
  posture_score?: number;
  movement_smoothness?: number;
  gait_symmetry?: number;
  movement_consistency?: number;
  peak_velocity?: number;
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
  
  assessment_status: 'VALID' | 'REPEAT_REQUIRED' | 'INSUFFICIENT_DATA';
  landmark_quality_score: number;
  valid_frame_ratio: number;
  movement_quality_score: number;
  validation_message?: string;

  movement_tests?: {
    knee_flexion?: MovementTestResult;
    sit_to_stand?: MovementTestResult;
    walking?: MovementTestResult;
  };

  min_left_knee_angle?: number;
  max_left_knee_angle?: number;
  mean_left_knee_angle?: number;
  median_left_knee_angle?: number;
  min_right_knee_angle?: number;
  max_right_knee_angle?: number;
  mean_right_knee_angle?: number;
  median_right_knee_angle?: number;
  rom_difference?: number;
  peak_left_velocity?: number;
  peak_right_velocity?: number;
  peak_velocity_difference?: number;
  movement_duration?: number;
  repetition_count?: number;
  signal_continuity_score?: number;
  temporal_stability_score?: number;
}

export interface RiskFactorItem {
  factor: string;
  importance: number;
  status: 'Optimal' | 'Moderate' | 'Alert' | string;
  detail: string;
  observed?: string;
  inference?: string;
  confidence_limitation?: string;
  feature_name?: string;
  actual_value?: number;
  scaled_value?: number;
  coefficient?: number;
  raw_contribution?: number;
  relative_attribution?: number | null;
  direction?: 'increases risk' | 'decreases risk' | string;
  predicted_class?: string;
}

export interface ScreeningQualityReport {
  assessment_quality: DataQualityCategory;
  camera_quality: DataQualityCategory;
  movement_capture: DataQualityCategory;
  feature_completeness: DataQualityCategory;
  ai_confidence: ConfidenceCategory;
  gate_decision?: 'PROCEED' | 'PROCEED_WITH_CAUTION' | 'REJECT_REPEAT_REQUIRED' | string;
  reason?: string;
  retest_recommended?: boolean;
  retest_recommendation?: string;
}

export interface ConfidenceBreakdown {
  model_confidence_pct: number;
  class_probability_margin: number;
  model_probability_margin?: number;
  assessment_quality: string;
  data_quality_level?: string;
  confidence_level: string;
  feature_completeness_ratio?: number;
  movement_reliability?: number;
}

export interface PredictionResult {
  risk_level: RiskLevel | string;
  risk_probability: number;
  confidence: number;
  confidence_level?: ConfidenceCategory;
  data_quality?: DataQualityCategory;
  confidence_reason?: string;
  confidence_breakdown?: ConfidenceBreakdown;
  quality_report?: ScreeningQualityReport;
  early_guidance?: string;
  questionnaire_contribution: number;
  movement_contribution: number;
  movement_indicator: 'Low' | 'Moderate' | 'High' | string;
  pain_mobility_indicator: 'Low' | 'Moderate' | 'High' | string;
  top_risk_factors: RiskFactorItem[];
  recommendations: string[];
  disclaimer: string;
  model_version: string;
  model_name?: string;
  assessment_status?: string;
  prediction_status?: string;
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
  assessment_status?: 'VALID' | 'REPEAT_REQUIRED' | 'INSUFFICIENT_DATA' | 'LIMITED_QUALITY' | string;
  landmark_quality_score?: number;
  valid_frame_ratio?: number;
  movement_quality_score?: number;
  validation_message?: string;
  min_left_knee_angle?: number;
  max_left_knee_angle?: number;
  mean_left_knee_angle?: number;
  median_left_knee_angle?: number;
  min_right_knee_angle?: number;
  max_right_knee_angle?: number;
  mean_right_knee_angle?: number;
  median_right_knee_angle?: number;
  rom_difference?: number;
  peak_left_velocity?: number;
  peak_right_velocity?: number;
  movement_duration?: number;
  repetition_count?: number;
  movement_tests?: {
    knee_flexion?: MovementTestResult;
    sit_to_stand?: MovementTestResult;
    walking?: MovementTestResult;
  };
  model_name?: string;
  prediction_status?: string;
  risk_level: RiskLevel | string;
  risk_probability: number;
  confidence: number;
  confidence_level?: ConfidenceCategory;
  data_quality?: DataQualityCategory;
  confidence_reason?: string;
  confidence_breakdown?: ConfidenceBreakdown;
  quality_report?: ScreeningQualityReport;
  early_guidance?: string;
  questionnaire_contribution: number;
  movement_contribution: number;
  notes?: string;
  sync_status: 'synced' | 'pending_sync' | 'sync_failed';
  model_version: string;
  created_at: string;
  updated_at?: string;
  report_id?: number;
}

export interface TrajectoryPoint {
  session_number: number;
  screening_id: number;
  screening_date: string;
  risk_level: RiskLevel;
  risk_probability: number;
  confidence: number;
  confidence_level: ConfidenceCategory;
  data_quality: DataQualityCategory;
  left_knee_rom: number;
  right_knee_rom: number;
  knee_symmetry: number;
  gait_symmetry: number;
  movement_smoothness: number;
  pain_score: number;
  mobility_score: number;
}

export interface RiskTrajectory {
  status: TrajectoryStatus;
  summary: string;
  trajectory_points: TrajectoryPoint[];
  comparison?: {
    sessions_compared: number;
    latest_risk: RiskLevel;
    previous_risk?: RiskLevel;
    rom_change: number;
    pain_change: number;
    mobility_change?: number;
    symmetry_change: number;
    probability_change?: number;
  };
}

export interface QRPassRecord {
  id: number;
  expires_at: string;
  is_revoked: boolean;
  access_count: number;
  last_accessed_at?: string;
  created_at: string;
}

export interface QRTokenData {
  qr_id: number;
  patient_id: number;
  patient_code: string;
  access_url: string;
  expires_at: string;
  is_revoked: boolean;
  access_count: number;
  created_at: string;
}

export interface QRAccessSummary {
  access_valid: boolean;
  token_expires_at: string;
  patient: {
    patient_code: string;
    name: string;
    age: number;
    gender: string;
    activity_level: string;
    doctor_notes?: string;
    referral_info?: string;
    follow_up_instructions?: string;
  };
  latest_screening?: {
    screening_date?: string;
    risk_level: RiskLevel;
    risk_probability: number;
    confidence_level: ConfidenceCategory;
    data_quality: DataQualityCategory;
    left_knee_rom: number;
    right_knee_rom: number;
    knee_symmetry: number;
    gait_symmetry: number;
    assessment_status: string;
    clinical_notes?: string;
  };
  disclaimer: string;
}

export interface AuditLogItem {
  id: number;
  timestamp: string;
  action: string;
  patient_id?: number;
  assessment_id?: number;
  status: string;
  source_ip?: string;
  details?: string;
}

export interface SyncQueueStatus {
  pending: number;
  syncing: number;
  synced: number;
  failed: number;
  conflict: number;
  total_queued: number;
  recent_records: Array<{
    id: number;
    entity_type: string;
    entity_id: number;
    sync_status: string;
    retry_count: number;
    last_error?: string;
    created_at?: string;
    synced_at?: string;
  }>;
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
