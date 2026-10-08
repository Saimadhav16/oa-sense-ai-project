import random
import string
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..database import get_db
from ..models import Patient, Screening, PatientQRAccess
from ..schemas import PatientCreate, PatientUpdate, PatientResponse, QRGenerateRequest, QRTokenResponse
from ..services.audit_service import log_audit_event, AuditAction
from ..services.trajectory_service import calculate_trajectory
from ..services.qr_service import (
    create_patient_qr_access,
    revoke_patient_qr_access
)

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
            "doctor_notes": p.doctor_notes,
            "referral_info": p.referral_info,
            "follow_up_instructions": p.follow_up_instructions,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "last_screening_risk": risk_lvl,
            "last_screening_date": last_date
        }
        results.append(p_dict)

    return results

@router.post("", response_model=PatientResponse)
def create_patient(patient_in: PatientCreate, request: Request, db: Session = Depends(get_db)):
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
        morning_stiffness=patient_in.morning_stiffness or 0,
        doctor_notes=patient_in.doctor_notes,
        referral_info=patient_in.referral_info,
        follow_up_instructions=patient_in.follow_up_instructions
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)

    client_ip = request.client.host if request.client else None
    log_audit_event(
        db=db,
        action=AuditAction.PATIENT_CREATED,
        patient_id=new_patient.id,
        status="SUCCESS",
        source_ip=client_ip,
        details={"patient_code": new_patient.patient_code}
    )

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
        "doctor_notes": new_patient.doctor_notes,
        "referral_info": new_patient.referral_info,
        "follow_up_instructions": new_patient.follow_up_instructions,
        "created_at": new_patient.created_at,
        "updated_at": new_patient.updated_at,
        "last_screening_risk": None,
        "last_screening_date": None
    }

@router.get("/{id}")
def get_patient_detail(id: int, request: Request, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    client_ip = request.client.host if request.client else None
    log_audit_event(
        db=db,
        action=AuditAction.PATIENT_VIEWED,
        patient_id=patient.id,
        status="SUCCESS",
        source_ip=client_ip
    )

    screenings = db.query(Screening).filter(Screening.patient_id == id).order_by(desc(Screening.screening_date)).all()
    history = []
    for s in screenings:
        history.append({
            "id": s.id,
            "screening_date": s.screening_date,
            "risk_level": s.risk_level,
            "risk_probability": s.risk_probability,
            "confidence": s.confidence,
            "confidence_level": s.confidence_level or "HIGH",
            "data_quality": s.data_quality or "GOOD",
            "confidence_reason": s.confidence_reason,
            "pain_score": s.pain_score,
            "mobility_score": s.mobility_score,
            "left_knee_rom": s.left_knee_rom,
            "right_knee_rom": s.right_knee_rom,
            "knee_symmetry": s.knee_symmetry,
            "gait_symmetry": s.gait_symmetry,
            "posture_score": s.posture_score,
            "assessment_status": s.assessment_status,
            "created_at": s.created_at
        })

    # Calculate transparent longitudinal risk trajectory
    trajectory = calculate_trajectory(screenings)

    # Active/historical QR tokens
    qr_records = db.query(PatientQRAccess).filter(
        PatientQRAccess.patient_id == patient.id
    ).order_by(desc(PatientQRAccess.created_at)).all()

    qr_list = [
        {
            "id": qr.id,
            "expires_at": qr.expires_at.isoformat(),
            "is_revoked": qr.is_revoked,
            "access_count": qr.access_count,
            "last_accessed_at": qr.last_accessed_at.isoformat() if qr.last_accessed_at else None,
            "created_at": qr.created_at.isoformat()
        }
        for qr in qr_records
    ]

    return {
        "patient": patient,
        "screenings": history,
        "trajectory": trajectory,
        "qr_passes": qr_list
    }

@router.put("/{id}", response_model=PatientResponse)
def update_patient(id: int, p_update: PatientUpdate, request: Request, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    for k, v in p_update.dict(exclude_unset=True).items():
        setattr(patient, k, v)

    db.commit()
    db.refresh(patient)

    client_ip = request.client.host if request.client else None
    log_audit_event(
        db=db,
        action=AuditAction.PATIENT_UPDATED,
        patient_id=patient.id,
        status="SUCCESS",
        source_ip=client_ip
    )

    return patient

@router.get("/{id}/trajectory")
def get_patient_trajectory(id: int, db: Session = Depends(get_db)):
    """Computes longitudinal screening risk-marker trajectory."""
    patient = db.query(Patient).filter(Patient.id == id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    screenings = db.query(Screening).filter(Screening.patient_id == id).all()
    trajectory = calculate_trajectory(screenings)
    return {
        "patient_id": patient.id,
        "patient_code": patient.patient_code,
        "trajectory": trajectory
    }

# --- Secure QR Access Management Endpoints ---
@router.post("/{id}/qr", response_model=QRTokenResponse)
def generate_patient_qr(
    id: int,
    req_body: QRGenerateRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Generates a cryptographically secure random token for authorized access to digital screening summary.
    The raw token is returned once for client QR rendering and is NOT stored in the database.
    The QR URL embeds ONLY the random opaque token.
    """
    patient = db.query(Patient).filter(Patient.id == id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    client_ip = request.client.host if request.client else None
    hours = req_body.expires_in_hours or 72

    raw_token, qr_record = create_patient_qr_access(
        db=db,
        patient_id=patient.id,
        expires_in_hours=hours,
        source_ip=client_ip
    )

    # Base URL construction (defaults to frontend /access/:token or api endpoint)
    # The token is opaque and contains NO medical/patient data
    access_url = f"/access/{raw_token}"

    return {
        "qr_id": qr_record.id,
        "patient_id": patient.id,
        "patient_code": patient.patient_code,
        "access_url": access_url,
        "expires_at": qr_record.expires_at,
        "is_revoked": qr_record.is_revoked,
        "access_count": qr_record.access_count,
        "created_at": qr_record.created_at
    }

@router.delete("/qr/{qr_id}/revoke")
def revoke_patient_qr(qr_id: int, request: Request, db: Session = Depends(get_db)):
    """Revokes an issued QR access token immediately."""
    client_ip = request.client.host if request.client else None
    revoked = revoke_patient_qr_access(db=db, qr_id=qr_id, source_ip=client_ip)
    if not revoked:
        raise HTTPException(status_code=404, detail="QR access record not found")
    return {"status": "REVOKED", "message": "QR access token revoked successfully."}
