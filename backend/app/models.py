import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
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

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    screenings = relationship("Screening", back_populates="patient", cascade="all, delete-orphan")

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

    # ML Output
    risk_level = Column(String(30), default="Low Risk")  # 'Low Risk', 'Moderate Risk', 'High Risk'
    risk_probability = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    questionnaire_contribution = Column(Float, default=50.0)
    movement_contribution = Column(Float, default=50.0)
    explainability_json = Column(Text, nullable=True)
    model_version = Column(String(50), default="1.0.0-demo")
    sync_status = Column(String(30), default="synced")  # 'synced', 'pending_sync', 'sync_failed'
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="screenings")
    movement_frames = relationship("MovementFrame", back_populates="screening", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="screening", cascade="all, delete-orphan")

class MovementFrame(Base):
    __tablename__ = "movement_frames"

    id = Column(Integer, primary_key=True, index=True)
    screening_id = Column(Integer, ForeignKey("screenings.id"), nullable=False)
    timestamp = Column(Float, nullable=False)
    left_knee_angle = Column(Float, nullable=False)
    right_knee_angle = Column(Float, nullable=False)
    hip_angle = Column(Float, nullable=True)
    posture_value = Column(Float, nullable=True)

    screening = relationship("Screening", back_populates="movement_frames")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    screening_id = Column(Integer, ForeignKey("screenings.id"), nullable=False)
    file_path = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    screening = relationship("Screening", back_populates="reports")
