import random
import string
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..database import get_db
from ..models import Patient, Screening
from ..schemas import PatientCreate, PatientUpdate, PatientResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/patients", tags=["Patients"])

def generate_patient_code() -> str:
    suffix = "".join(random.choices(string.digits, k=4))
    return f"OA-2026-{suffix}"

@router.get("", response_model=List[PatientResponse])
def get_patients(
    search: Optional[str] = None,
    risk_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Patient)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Patient.name.ilike(s)) | (Patient.patient_code.ilike(s)) | (Patient.phone.ilike(s)))

    patients = query.order_by(desc(Patient.created_at)).offset(skip).limit(limit).all()

    # Populate latest screening risk indicator
    results = []
    for p in patients:
        latest_scr = db.query(Screening).filter(Screening.patient_id == p.id).order_by(desc(Screening.screening_date)).first()
        risk_lvl = latest_scr.risk_level if latest_scr else None
        last_date = latest_scr.screening_date if latest_scr else None

        if risk_filter and risk_filter.lower() != "all":
            if not risk_lvl or risk_filter.lower() not in risk_lvl.lower():
                continue

        p_dict = {
            "id": p.id,
            "patient_code": p.patient_code,
            "name": p.name,
            "age": p.age,
            "gender": p.gender,
            "phone": p.phone,
            "location": p.location,
            "occupation": p.occupation,
            "activity_level": p.activity_level,
            "joint_injury": p.joint_injury,
            "family_history": p.family_history,
            "demanding_work": p.demanding_work,
            "walking_difficulty": p.walking_difficulty,
            "stair_difficulty": p.stair_difficulty,
            "morning_stiffness": p.morning_stiffness,
            "created_at": p.created_at,
            "last_screening_risk": risk_lvl,
            "last_screening_date": last_date
        }
        results.append(p_dict)

    return results

@router.post("", response_model=PatientResponse)
def create_patient(patient_in: PatientCreate, db: Session = Depends(get_db)):
    code = patient_in.patient_code.strip() if patient_in.patient_code else generate_patient_code()
    
    # Check code uniqueness
    existing = db.query(Patient).filter(Patient.patient_code == code).first()
    if existing:
        code = generate_patient_code()

    new_patient = Patient(
        patient_code=code,
        name=patient_in.name,
        age=patient_in.age,
        gender=patient_in.gender,
        phone=patient_in.phone,
        location=patient_in.location,
        occupation=patient_in.occupation,
        activity_level=patient_in.activity_level or "Moderate",
        joint_injury=patient_in.joint_injury or 0,
        family_history=patient_in.family_history or 0,
        demanding_work=patient_in.demanding_work or 0,
        walking_difficulty=patient_in.walking_difficulty or 0,
        stair_difficulty=patient_in.stair_difficulty or 0,
        morning_stiffness=patient_in.morning_stiffness or 0
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)

    return {
        "id": new_patient.id,
        "patient_code": new_patient.patient_code,
        "name": new_patient.name,
        "age": new_patient.age,
        "gender": new_patient.gender,
        "phone": new_patient.phone,
        "location": new_patient.location,
        "occupation": new_patient.occupation,
        "activity_level": new_patient.activity_level,
        "joint_injury": new_patient.joint_injury,
        "family_history": new_patient.family_history,
        "demanding_work": new_patient.demanding_work,
        "walking_difficulty": new_patient.walking_difficulty,
        "stair_difficulty": new_patient.stair_difficulty,
        "morning_stiffness": new_patient.morning_stiffness,
        "created_at": new_patient.created_at,
        "last_screening_risk": None,
        "last_screening_date": None
    }

@router.get("/{id}")
def get_patient_detail(id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    screenings = db.query(Screening).filter(Screening.patient_id == id).order_by(desc(Screening.screening_date)).all()
    history = []
    for s in screenings:
        history.append({
            "id": s.id,
            "screening_date": s.screening_date,
            "risk_level": s.risk_level,
            "risk_probability": s.risk_probability,
            "pain_score": s.pain_score,
            "mobility_score": s.mobility_score,
            "left_knee_rom": s.left_knee_rom,
            "right_knee_rom": s.right_knee_rom,
            "gait_symmetry": s.gait_symmetry,
            "posture_score": s.posture_score,
            "created_at": s.created_at
        })

    return {
        "patient": patient,
        "screenings": history
    }

@router.put("/{id}", response_model=PatientResponse)
def update_patient(id: int, p_update: PatientUpdate, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    for k, v in p_update.dict(exclude_unset=True).items():
        setattr(patient, k, v)

    db.commit()
    db.refresh(patient)
    return patient
