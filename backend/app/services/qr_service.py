import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from ..models import Patient, PatientQRAccess, Screening
from .audit_service import log_audit_event, AuditAction

TOKEN_BYTE_LENGTH = 32  # 256 bits of cryptographic entropy
DEFAULT_QR_EXPIRATION_HOURS = 72  # 3 days validity

def hash_token(raw_token: str) -> str:
    """Computes SHA-256 hash of access token for secure database storage."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

def create_patient_qr_access(
    db: Session,
    patient_id: int,
    expires_in_hours: int = DEFAULT_QR_EXPIRATION_HOURS,
    source_ip: Optional[str] = None
) -> Tuple[str, PatientQRAccess]:
    """
    Generates a cryptographically secure random token, hashes it,
    stores hash in database, and returns (raw_token, access_record).
    The raw token is NEVER stored in the database.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise ValueError("Patient not found")

    raw_token = secrets.token_urlsafe(TOKEN_BYTE_LENGTH)
    t_hash = hash_token(raw_token)
    expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

    record = PatientQRAccess(
        patient_id=patient.id,
        token_hash=t_hash,
        expires_at=expires_at,
        is_revoked=False,
        access_count=0
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    log_audit_event(
        db=db,
        action=AuditAction.QR_CREATED,
        patient_id=patient.id,
        status="SUCCESS",
        source_ip=source_ip,
        details={
            "qr_record_id": record.id,
            "expires_at": expires_at.isoformat()
        }
    )

    return raw_token, record

def revoke_patient_qr_access(
    db: Session,
    qr_id: int,
    source_ip: Optional[str] = None
) -> bool:
    """Revokes an existing QR access record."""
    record = db.query(PatientQRAccess).filter(PatientQRAccess.id == qr_id).first()
    if not record:
        return False

    record.is_revoked = True
    db.commit()

    log_audit_event(
        db=db,
        action=AuditAction.QR_REVOKED,
        patient_id=record.patient_id,
        status="SUCCESS",
        source_ip=source_ip,
        details={"qr_record_id": record.id}
    )
    return True

def validate_and_resolve_qr_token(
    db: Session,
    raw_token: str,
    source_ip: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validates provided raw token against hashed records.
    Enforces expiration, revocation, rate/access checks, and audit logging.
    Returns sanitized digital screening summary (NO credentials, NO internal IDs).
    """
    if not raw_token or len(raw_token) < 16:
        log_audit_event(
            db=db,
            action=AuditAction.QR_ACCESSED,
            status="FAILED",
            source_ip=source_ip,
            details={"reason": "Invalid token format"}
        )
        raise ValueError("Invalid QR access token format.")

    t_hash = hash_token(raw_token)
    record = db.query(PatientQRAccess).filter(PatientQRAccess.token_hash == t_hash).first()

    if not record:
        log_audit_event(
            db=db,
            action=AuditAction.QR_ACCESSED,
            status="FAILED",
            source_ip=source_ip,
            details={"reason": "Token not found"}
        )
        raise ValueError("QR access token not found or invalid.")

    if record.is_revoked:
        log_audit_event(
            db=db,
            action=AuditAction.QR_ACCESSED,
            patient_id=record.patient_id,
            status="FAILED",
            source_ip=source_ip,
            details={"reason": "Token revoked", "qr_record_id": record.id}
        )
        raise ValueError("This QR access pass has been revoked by healthcare provider.")

    if datetime.utcnow() > record.expires_at:
        log_audit_event(
            db=db,
            action=AuditAction.QR_ACCESSED,
            patient_id=record.patient_id,
            status="FAILED",
            source_ip=source_ip,
            details={"reason": "Token expired", "qr_record_id": record.id}
        )
        raise ValueError("This QR access pass has expired. Please request a new access pass.")

    # Record successful access
    record.access_count += 1
    record.last_accessed_at = datetime.utcnow()
    db.commit()

    patient = db.query(Patient).filter(Patient.id == record.patient_id).first()
    latest_screening = db.query(Screening).filter(
        Screening.patient_id == patient.id
    ).order_by(Screening.screening_date.desc()).first()

    log_audit_event(
        db=db,
        action=AuditAction.QR_ACCESSED,
        patient_id=patient.id,
        assessment_id=latest_screening.id if latest_screening else None,
        status="SUCCESS",
        source_ip=source_ip,
        details={
            "qr_record_id": record.id,
            "access_count": record.access_count
        }
    )

    # Return safe patient digital screening summary
    # Strictly excludes credentials, sensitive contact info, database password
    return {
        "access_valid": True,
        "token_expires_at": record.expires_at.isoformat(),
        "patient": {
            "patient_code": patient.patient_code,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "activity_level": patient.activity_level,
            "doctor_notes": patient.doctor_notes,
            "referral_info": patient.referral_info,
            "follow_up_instructions": patient.follow_up_instructions
        },
        "latest_screening": {
            "screening_date": (latest_screening.screening_date or latest_screening.created_at).isoformat() if latest_screening else None,
            "risk_level": latest_screening.risk_level if latest_screening else "N/A",
            "risk_probability": latest_screening.risk_probability if latest_screening else 0.0,
            "confidence_level": latest_screening.confidence_level if latest_screening else "HIGH",
            "data_quality": latest_screening.data_quality if latest_screening else "GOOD",
            "left_knee_rom": latest_screening.left_knee_rom if latest_screening else 0.0,
            "right_knee_rom": latest_screening.right_knee_rom if latest_screening else 0.0,
            "knee_symmetry": latest_screening.knee_symmetry if latest_screening else 100.0,
            "gait_symmetry": latest_screening.gait_symmetry if latest_screening else 100.0,
            "assessment_status": latest_screening.assessment_status if latest_screening else "VALID",
            "clinical_notes": latest_screening.notes if latest_screening else None
        } if latest_screening else None,
        "disclaimer": (
            "IMPORTANT MEDICAL NOTICE: This digital summary is an AI-assisted preliminary screening record. "
            "It does not constitute a clinical medical diagnosis. Please present to your healthcare provider for evaluation."
        )
    }
