import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="healthcare_worker")  # 'admin', 'healthcare_worker'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    phone = Column(String(30), nullable=True)
    location = Column(String(150), nullable=True)
    occupation = Column(String(100), nullable=True)
    activity_level = Column(String(50), default="Moderate")
    
    # Risk factor history
    joint_injury = Column(Integer, default=0)
    family_history = Column(Integer, default=0)
    demanding_work = Column(Integer, default=0)
    walking_difficulty = Column(Integer, default=0)
    stair_difficulty = Column(Integer, default=0)
    morning_stiffness = Column(Integer, default=0)

    # Secure digital patient record extensions
    doctor_notes = Column(Text, nullable=True)
    referral_info = Column(Text, nullable=True)
    follow_up_instructions = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    screenings = relationship("Screening", back_populates="patient", cascade="all, delete-orphan")
    qr_access_tokens = relationship("PatientQRAccess", back_populates="patient", cascade="all, delete-orphan")

class Screening(Base):
    __tablename__ = "screenings"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    screening_date = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Questionnaire summary scores
    pain_score = Column(Float, default=0.0)
    stiffness_score = Column(Float, default=0.0)
    mobility_score = Column(Float, default=10.0)
    questionnaire_json = Column(Text, nullable=True)

    # Computer Vision derived movement features
    left_knee_rom = Column(Float, default=0.0)
    right_knee_rom = Column(Float, default=0.0)
    knee_symmetry = Column(Float, default=100.0)
    average_knee_angle = Column(Float, default=180.0)
    gait_symmetry = Column(Float, default=100.0)
    movement_consistency = Column(Float, default=100.0)
    posture_score = Column(Float, default=100.0)
    hip_movement = Column(Float, default=0.0)
    ankle_movement = Column(Float, default=0.0)
    movement_smoothness = Column(Float, default=100.0)
    # Landmark Validation Metrics
    assessment_status = Column(String(30), default="VALID")  # 'VALID', 'REPEAT_REQUIRED', 'INSUFFICIENT_DATA'
    landmark_quality_score = Column(Float, default=100.0)
    valid_frame_ratio = Column(Float, default=1.0)
    movement_quality_score = Column(Float, default=100.0)
    validation_message = Column(Text, nullable=True)

    # Time-Series Kinematic Dynamics
    min_left_knee_angle = Column(Float, nullable=True)
    max_left_knee_angle = Column(Float, nullable=True)
    mean_left_knee_angle = Column(Float, nullable=True)
    median_left_knee_angle = Column(Float, nullable=True)
    min_right_knee_angle = Column(Float, nullable=True)
    max_right_knee_angle = Column(Float, nullable=True)
    mean_right_knee_angle = Column(Float, nullable=True)
    median_right_knee_angle = Column(Float, nullable=True)
    rom_difference = Column(Float, nullable=True)
    peak_left_velocity = Column(Float, nullable=True)
    peak_right_velocity = Column(Float, nullable=True)
    movement_duration = Column(Float, nullable=True)
    repetition_count = Column(Integer, nullable=True)

    # ML Output & Confidence-Aware AI
    risk_level = Column(String(30), default="Low Risk")  # 'Low Risk', 'Moderate Risk', 'High Risk'
    risk_probability = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    confidence_level = Column(String(20), default="HIGH")  # 'HIGH', 'MEDIUM', 'LOW'
    data_quality = Column(String(20), default="GOOD")  # 'GOOD', 'FAIR', 'POOR'
    confidence_reason = Column(Text, nullable=True)
    quality_report_json = Column(Text, nullable=True)
    early_guidance = Column(Text, nullable=True)
    confidence_breakdown_json = Column(Text, nullable=True)
    questionnaire_contribution = Column(Float, default=50.0)
    movement_contribution = Column(Float, default=50.0)
    explainability_json = Column(Text, nullable=True)
    model_version = Column(String(50), default="1.0.0-demo")
    model_name = Column(String(50), default="LogisticRegression")
    prediction_status = Column(String(30), default="COMPLETED")
    sync_status = Column(String(30), default="synced")  # 'synced', 'pending_sync', 'sync_failed'
    movement_tests_json = Column(Text, nullable=True)  # Detailed per-test metrics: Knee Flexion, Sit-to-Stand, Walking
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="screenings")
    movement_frames = relationship("MovementFrame", back_populates="screening", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="screening", cascade="all, delete-orphan")

class MovementFrame(Base):
    __tablename__ = "movement_frames"

    id = Column(Integer, primary_key=True, index=True)
    screening_id = Column(Integer, ForeignKey("screenings.id"), nullable=False)
    movement_type = Column(String(50), default="KNEE_FLEXION")  # KNEE_FLEXION, SIT_TO_STAND, WALKING
    timestamp = Column(Float, nullable=False)
    left_knee_angle = Column(Float, nullable=False)
    right_knee_angle = Column(Float, nullable=False)
    hip_angle = Column(Float, nullable=True)
    posture_value = Column(Float, nullable=True)
    frame_valid = Column(Boolean, default=True)
    phase = Column(String(30), nullable=True)

    screening = relationship("Screening", back_populates="movement_frames")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    screening_id = Column(Integer, ForeignKey("screenings.id"), nullable=False)
    file_path = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    screening = relationship("Screening", back_populates="reports")

class PatientQRAccess(Base):
    __tablename__ = "patient_qr_access"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    access_count = Column(Integer, default=0, nullable=False)
    last_accessed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="qr_access_tokens")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    action = Column(String(60), nullable=False, index=True)
    patient_id = Column(Integer, nullable=True, index=True)
    assessment_id = Column(Integer, nullable=True, index=True)
    status = Column(String(30), default="SUCCESS")  # 'SUCCESS', 'FAILED', 'WARNING'
    source_ip = Column(String(45), nullable=True)
    details = Column(Text, nullable=True)  # JSON-safe sanitized details, NEVER secrets/keys

class SyncRecord(Base):
    __tablename__ = "sync_records"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(40), nullable=False)  # 'patient', 'screening'
    entity_id = Column(Integer, nullable=False)
    sync_status = Column(String(30), default="PENDING", index=True)  # PENDING, SYNCING, SYNCED, FAILED, CONFLICT
    retry_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    synced_at = Column(DateTime, nullable=True)
