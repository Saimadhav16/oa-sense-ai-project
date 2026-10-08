from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# --- Auth Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_name: str
    user_email: str
    role: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Patient Schemas ---
class PatientBase(BaseModel):
    patient_code: Optional[str] = None
    name: str
    age: int
    gender: str
    phone: Optional[str] = None
    location: Optional[str] = None
    occupation: Optional[str] = None
    activity_level: Optional[str] = "Moderate"
    joint_injury: Optional[int] = 0
    family_history: Optional[int] = 0
    demanding_work: Optional[int] = 0
    walking_difficulty: Optional[int] = 0
    stair_difficulty: Optional[int] = 0
    morning_stiffness: Optional[int] = 0
    # Digital Record Fields
    doctor_notes: Optional[str] = None
    referral_info: Optional[str] = None
    follow_up_instructions: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    occupation: Optional[str] = None
    activity_level: Optional[str] = None
    joint_injury: Optional[int] = None
    family_history: Optional[int] = None
    demanding_work: Optional[int] = None
    walking_difficulty: Optional[int] = None
    stair_difficulty: Optional[int] = None
    morning_stiffness: Optional[int] = None
    doctor_notes: Optional[str] = None
    referral_info: Optional[str] = None
    follow_up_instructions: Optional[str] = None

class PatientResponse(PatientBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_screening_risk: Optional[str] = None
    last_screening_date: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- Questionnaire Schemas ---
class QuestionnaireInput(BaseModel):
    knee_pain: int = Field(..., ge=0, le=4, description="0=Never, 1=Rarely, 2=Sometimes, 3=Often, 4=Always")
    joint_stiffness: int = Field(..., ge=0, le=4)
    walking_difficulty: int = Field(..., ge=0, le=4)
    stair_difficulty: int = Field(..., ge=0, le=4)
    standing_difficulty: int = Field(..., ge=0, le=4)
    knee_bending_difficulty: int = Field(..., ge=0, le=4)
    pain_increase_activity: int = Field(..., ge=0, le=4)
    pain_scale: float = Field(..., ge=0.0, le=10.0, description="0-10 subjective pain intensity")
    mobility_scale: float = Field(..., ge=0.0, le=10.0, description="0-10 self-rated mobility rating")

class QuestionnaireAnalysisResponse(BaseModel):
    pain_score: float
    stiffness_score: float
    mobility_score: float
    walking_difficulty: int
    stair_difficulty: int
    preliminary_symptom_risk: str
    interpretation: str

# --- Movement & CV Schemas ---
class MovementFrameData(BaseModel):
    timestamp: float
    left_knee_angle: float
    right_knee_angle: float
    hip_angle: Optional[float] = None
    posture_value: Optional[float] = None
    frame_valid: Optional[bool] = True
    phase: Optional[str] = None
    movement_type: Optional[str] = "KNEE_FLEXION"

class MovementSummaryInput(BaseModel):
    left_knee_rom: float
    right_knee_rom: float
    knee_symmetry: float
    average_knee_angle: float
    gait_symmetry: float
    movement_consistency: float
    posture_score: float
    hip_movement: float
    ankle_movement: float
    movement_smoothness: float
    # Landmark Validation Fields
    assessment_status: Optional[str] = "VALID"  # 'VALID', 'REPEAT_REQUIRED', 'INSUFFICIENT_DATA'
    landmark_quality_score: Optional[float] = 100.0
    valid_frame_ratio: Optional[float] = 1.0
    movement_quality_score: Optional[float] = 100.0
    validation_message: Optional[str] = None
    # Real Time-Series Kinematics
    min_left_knee_angle: Optional[float] = None
    max_left_knee_angle: Optional[float] = None
    mean_left_knee_angle: Optional[float] = None
    median_left_knee_angle: Optional[float] = None
    min_right_knee_angle: Optional[float] = None
    max_right_knee_angle: Optional[float] = None
    mean_right_knee_angle: Optional[float] = None
    median_right_knee_angle: Optional[float] = None
    rom_difference: Optional[float] = None
    peak_left_velocity: Optional[float] = None
    peak_right_velocity: Optional[float] = None
    peak_velocity_difference: Optional[float] = None
    movement_duration: Optional[float] = None
    repetition_count: Optional[int] = None
    signal_continuity_score: Optional[float] = None
    temporal_stability_score: Optional[float] = None
    movement_tests: Optional[Dict[str, Any]] = None
    frames: Optional[List[MovementFrameData]] = None

# --- ML Prediction & Explainability Schemas ---
class RiskFactorItem(BaseModel):
    factor: str
    importance: float
    status: str
    detail: str
    observed: Optional[str] = None
    inference: Optional[str] = None
    confidence_limitation: Optional[str] = None
    feature_name: Optional[str] = None
    actual_value: Optional[float] = None
    scaled_value: Optional[float] = None
    coefficient: Optional[float] = None
    raw_contribution: Optional[float] = None
    relative_attribution: Optional[float] = None
    direction: Optional[str] = None
    predicted_class: Optional[str] = None

class PredictionRequest(BaseModel):
    patient_id: Optional[int] = None
    age: int
    activity_level: str
    joint_injury: int = 0
    family_history: int = 0
    questionnaire: QuestionnaireInput
    movement: MovementSummaryInput

class PredictionResponse(BaseModel):
    risk_level: str  # 'Low Risk', 'Moderate Risk', 'High Risk'
    risk_probability: float  # 0 - 100 percentage
    confidence: float  # 0 - 100 percentage
    confidence_level: Optional[str] = "HIGH"  # 'HIGH', 'MEDIUM', 'LOW'
    data_quality: Optional[str] = "GOOD"  # 'GOOD', 'FAIR', 'POOR'
    confidence_reason: Optional[str] = None
    confidence_breakdown: Optional[Dict[str, Any]] = None
    quality_report: Optional[Dict[str, Any]] = None
    early_guidance: Optional[str] = None
    questionnaire_contribution: float  # percentage
    movement_contribution: float  # percentage
    movement_indicator: str  # 'Low', 'Moderate', 'High'
    pain_mobility_indicator: str  # 'Low', 'Moderate', 'High'
    top_risk_factors: List[RiskFactorItem]
    recommendations: List[str]
    disclaimer: str
    model_version: str
    model_name: Optional[str] = "LogisticRegression"
    assessment_status: Optional[str] = "VALID"
    prediction_status: Optional[str] = "COMPLETED"

# --- Screening Record Schemas ---
class ScreeningCreate(BaseModel):
    patient_id: int
    questionnaire: QuestionnaireInput
    movement: MovementSummaryInput
    notes: Optional[str] = None
    sync_status: Optional[str] = "synced"

class ScreeningResponse(BaseModel):
    id: int
    patient_id: int
    patient_name: Optional[str] = None
    patient_code: Optional[str] = None
    screening_date: datetime
    pain_score: float
    stiffness_score: float
    mobility_score: float
    left_knee_rom: float
    right_knee_rom: float
    knee_symmetry: float
    average_knee_angle: float
    gait_symmetry: float
    movement_consistency: float
    posture_score: float
    movement_smoothness: float
    assessment_status: Optional[str] = "VALID"
    landmark_quality_score: Optional[float] = 100.0
    valid_frame_ratio: Optional[float] = 1.0
    movement_quality_score: Optional[float] = 100.0
    validation_message: Optional[str] = None
    min_left_knee_angle: Optional[float] = None
    max_left_knee_angle: Optional[float] = None
    mean_left_knee_angle: Optional[float] = None
    median_left_knee_angle: Optional[float] = None
    min_right_knee_angle: Optional[float] = None
    max_right_knee_angle: Optional[float] = None
    mean_right_knee_angle: Optional[float] = None
    median_right_knee_angle: Optional[float] = None
    rom_difference: Optional[float] = None
    peak_left_velocity: Optional[float] = None
    peak_right_velocity: Optional[float] = None
    movement_duration: Optional[float] = None
    repetition_count: Optional[int] = None
    movement_tests: Optional[Dict[str, Any]] = None
    model_name: Optional[str] = "LogisticRegression"
    prediction_status: Optional[str] = "COMPLETED"
    risk_level: str
    risk_probability: float
    confidence: float
    confidence_level: Optional[str] = "HIGH"
    data_quality: Optional[str] = "GOOD"
    confidence_reason: Optional[str] = None
    confidence_breakdown: Optional[Dict[str, Any]] = None
    quality_report: Optional[Dict[str, Any]] = None
    early_guidance: Optional[str] = None
    questionnaire_contribution: float
    movement_contribution: float
    top_risk_factors: Optional[List[RiskFactorItem]] = None
    explainability_json: Optional[str] = None
    notes: Optional[str] = None
    sync_status: str
    model_version: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    report_id: Optional[int] = None

    class Config:
        from_attributes = True

# --- QR Schemas ---
class QRGenerateRequest(BaseModel):
    expires_in_hours: Optional[int] = 72

class QRTokenResponse(BaseModel):
    qr_id: int
    patient_id: int
    patient_code: str
    access_url: str
    expires_at: datetime
    is_revoked: bool
    access_count: int
    created_at: datetime

class QRAccessSummaryResponse(BaseModel):
    access_valid: bool
    token_expires_at: str
    patient: Dict[str, Any]
    latest_screening: Optional[Dict[str, Any]] = None
    disclaimer: str

# --- Audit & Sync Schemas ---
class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    action: str
    patient_id: Optional[int] = None
    assessment_id: Optional[int] = None
    status: str
    source_ip: Optional[str] = None
    details: Optional[str] = None

    class Config:
        from_attributes = True

class SyncQueueStatusResponse(BaseModel):
    pending: int
    syncing: int
    synced: int
    failed: int
    conflict: int
    total_queued: int
    recent_records: List[Dict[str, Any]]

# --- Dashboard Stats Schemas ---
class DashboardStatistics(BaseModel):
    total_patients: int
    screenings_today: int
    high_risk_cases: int
    moderate_risk_cases: int
    low_risk_cases: int
    risk_distribution: Dict[str, int]
    recent_activity: List[Dict[str, Any]]
