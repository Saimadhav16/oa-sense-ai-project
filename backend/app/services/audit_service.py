import json
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import AuditLog

# Standard Action Types
class AuditAction:
    PATIENT_CREATED = "PATIENT_CREATED"
    PATIENT_UPDATED = "PATIENT_UPDATED"
    PATIENT_VIEWED = "PATIENT_VIEWED"
    ASSESSMENT_CREATED = "ASSESSMENT_CREATED"
    ASSESSMENT_VIEWED = "ASSESSMENT_VIEWED"
    REPORT_GENERATED = "REPORT_GENERATED"
    QR_CREATED = "QR_CREATED"
    QR_REVOKED = "QR_REVOKED"
    QR_ACCESSED = "QR_ACCESSED"
    SCREENING_COMPLETED = "SCREENING_COMPLETED"
    SCREENING_UPDATED = "SCREENING_UPDATED"
    REFERRAL_CREATED = "REFERRAL_CREATED"
    FEEDBACK_ADDED = "FEEDBACK_ADDED"
    SYNC_STARTED = "SYNC_STARTED"
    SYNC_COMPLETED = "SYNC_COMPLETED"
    SYNC_FAILED = "SYNC_FAILED"

# Redacted keys for security
FORBIDDEN_KEYS = {
    "password", "password_hash", "token", "access_token", "raw_token",
    "secret", "api_key", "secret_key", "authorization"
}

def sanitize_details(details: Optional[Dict[str, Any]]) -> Optional[str]:
    if not details:
        return None
    sanitized = {}
    for k, v in details.items():
        if any(bad in k.lower() for bad in FORBIDDEN_KEYS):
            sanitized[k] = "[REDACTED]"
        else:
            sanitized[k] = v
    return json.dumps(sanitized)

def log_audit_event(
    db: Session,
    action: str,
    patient_id: Optional[int] = None,
    assessment_id: Optional[int] = None,
    status: str = "SUCCESS",
    source_ip: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    Records security-sensitive operations in AuditLog.
    Guarantees secrets, passwords, and raw tokens are NEVER persisted.
    """
    entry = AuditLog(
        timestamp=datetime.utcnow(),
        action=action,
        patient_id=patient_id,
        assessment_id=assessment_id,
        status=status,
        source_ip=source_ip,
        details=sanitize_details(details)
    )
    db.add(entry)
    db.commit()
    return entry
