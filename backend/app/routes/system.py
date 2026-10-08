from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..database import get_db
from ..models import AuditLog
from ..schemas import AuditLogResponse, QRAccessSummaryResponse, SyncQueueStatusResponse
from ..services.qr_service import validate_and_resolve_qr_token
from ..services.sync_service import get_sync_queue_status, retry_failed_sync_records

router = APIRouter(prefix="/api", tags=["Security & System Services"])

@router.get("/access/qr/{token}", response_model=QRAccessSummaryResponse)
def access_patient_record_by_qr(token: str, request: Request, db: Session = Depends(get_db)):
    """
    Validates cryptographically secure random token, checks expiration and revocation,
    records access in AuditLog, and serves allowed digital screening summary.
    Never exposes internal IDs, passwords, or patient contact info.
    """
    client_ip = request.client.host if request.client else None
    try:
        data = validate_and_resolve_qr_token(db=db, raw_token=token, source_ip=client_ip)
        return data
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = None,
    patient_id: Optional[int] = None,
    limit: int = 50,
    skip: int = 0,
    db: Session = Depends(get_db)
):
    """Retrieves immutable audit events. Contains no passwords or access secrets."""
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if patient_id:
        query = query.filter(AuditLog.patient_id == patient_id)

    logs = query.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit).all()
    return logs

@router.get("/sync/queue", response_model=SyncQueueStatusResponse)
def get_sync_queue(db: Session = Depends(get_db)):
    """Retrieves current offline sync queue metrics and status."""
    return get_sync_queue_status(db)

@router.post("/sync/retry")
def retry_failed_sync(db: Session = Depends(get_db)):
    """Requeues failed offline sync queue entries."""
    return retry_failed_sync_records(db)
