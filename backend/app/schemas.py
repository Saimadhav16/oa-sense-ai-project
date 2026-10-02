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

class PatientResponse(PatientBase):
    id: int
    created_at: datetime
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
    frames: Optional[List[MovementFrameData]] = None

# --- ML Prediction Schemas ---
class PredictionRequest(BaseModel):
    patient_id: Optional[int] = None
    age: int
    activity_level: str
    joint_injury: int = 0
    family_history: int = 0
    questionnaire: QuestionnaireInput
    movement: MovementSummaryInput

class RiskFactorItem(BaseModel):
    factor: str
    importance: float
    status: str
    detail: str

class PredictionResponse(BaseModel):
    risk_level: str  # 'Low Risk', 'Moderate Risk', 'High Risk'
    risk_probability: float  # 0 - 100 percentage
    confidence: float  # 0 - 100 percentage
    questionnaire_contribution: float  # percentage
    movement_contribution: float  # percentage
    movement_indicator: str  # 'Low', 'Moderate', 'High'
    pain_mobility_indicator: str  # 'Low', 'Moderate', 'High'
    top_risk_factors: List[RiskFactorItem]
    recommendations: List[str]
    disclaimer: str
    model_version: str

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
    risk_level: str
    risk_probability: float
    confidence: float
    questionnaire_contribution: float
    movement_contribution: float
    notes: Optional[str] = None
    sync_status: str
    model_version: str
    created_at: datetime
    report_id: Optional[int] = None

    class Config:
        from_attributes = True

# --- Dashboard Stats Schemas ---
class DashboardStatistics(BaseModel):
    total_patients: int
    screenings_today: int
    high_risk_cases: int
    moderate_risk_cases: int
    low_risk_cases: int
    risk_distribution: Dict[str, int]
    recent_activity: List[Dict[str, Any]]
