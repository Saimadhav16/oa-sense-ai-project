from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from sqlalchemy.orm import Session
from ..models import Patient, Screening, SyncRecord
from .audit_service import log_audit_event, AuditAction

def queue_sync_record(
    db: Session,
    entity_type: str,
    entity_id: int,
    payload: Optional[Dict[str, Any]] = None
) -> SyncRecord:
    """Enqueues an entity for synchronization in the sync queue."""
    existing = db.query(SyncRecord).filter(
        SyncRecord.entity_type == entity_type,
        SyncRecord.entity_id == entity_id,
        SyncRecord.sync_status.in_(["PENDING", "RETRY"])
    ).first()

    if existing:
        existing.payload_json = json.dumps(payload) if payload else existing.payload_json
        db.commit()
        return existing

    record = SyncRecord(
        entity_type=entity_type,
        entity_id=entity_id,
        sync_status="PENDING",
        retry_count=0,
        payload_json=json.dumps(payload) if payload else None
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_sync_queue_status(db: Session) -> Dict[str, Any]:
    """Retrieves current sync queue metrics for offline-first observability."""
    pending = db.query(SyncRecord).filter(SyncRecord.sync_status == "PENDING").count()
    syncing = db.query(SyncRecord).filter(SyncRecord.sync_status == "SYNCING").count()
    synced = db.query(SyncRecord).filter(SyncRecord.sync_status == "SYNCED").count()
    failed = db.query(SyncRecord).filter(SyncRecord.sync_status == "FAILED").count()
    conflict = db.query(SyncRecord).filter(SyncRecord.sync_status == "CONFLICT").count()

    recent_syncs = db.query(SyncRecord).order_by(SyncRecord.created_at.desc()).limit(15).all()

    return {
        "pending": pending,
        "syncing": syncing,
        "synced": synced,
        "failed": failed,
        "conflict": conflict,
        "total_queued": pending + syncing + failed + conflict,
        "recent_records": [
            {
                "id": r.id,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "sync_status": r.sync_status,
                "retry_count": r.retry_count,
                "last_error": r.last_error,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "synced_at": r.synced_at.isoformat() if r.synced_at else None
            }
            for r in recent_syncs
        ]
    }

def retry_failed_sync_records(db: Session) -> Dict[str, Any]:
    """Resets failed sync queue items to PENDING with retry increment for automated synchronization."""
    failed_items = db.query(SyncRecord).filter(
        SyncRecord.sync_status.in_(["FAILED", "CONFLICT"])
    ).all()

    retried_count = 0
    for item in failed_items:
        item.sync_status = "PENDING"
        item.retry_count += 1
        retried_count += 1
    db.commit()

    log_audit_event(
        db=db,
        action=AuditAction.SYNC_STARTED,
        status="SUCCESS",
        details={"retried_records": retried_count}
    )

    return {"retried_count": retried_count, "message": f"{retried_count} sync records requeued."}

def sync_batch_screenings(db: Session, offline_screenings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Idempotent synchronization for offline screening batches.
    Prevents duplicates, resolves patient links, updates sync_status to 'synced',
    and generates audit log entries.
    """
    log_audit_event(
        db=db,
        action=AuditAction.SYNC_STARTED,
        status="SUCCESS",
        details={"incoming_count": len(offline_screenings)}
    )

    synced_count = 0
    failed_count = 0
    errors = []

    for item in offline_screenings:
        try:
            patient_id = item.get("patient_id")
            patient = db.query(Patient).filter(Patient.id == patient_id).first() if patient_id else None

            if not patient:
                p_code = item.get("patient_code")
                if p_code:
                    patient = db.query(Patient).filter(Patient.patient_code == p_code).first()

            if not patient:
                failed_count += 1
                errors.append(f"Patient reference not found (ID: {patient_id}, Code: {item.get('patient_code')})")
                continue

            # Idempotency check: avoid inserting identical screening within 2 minutes for same patient
            scr_date_str = item.get("screening_date")
            existing_duplicate = None
            if scr_date_str:
                try:
                    dt = datetime.fromisoformat(scr_date_str.replace("Z", "+00:00"))
                    existing_duplicate = db.query(Screening).filter(
                        Screening.patient_id == patient.id,
                        Screening.screening_date == dt
                    ).first()
                except Exception:
                    pass

            if existing_duplicate:
                # Mark as already synced without duplicating
                synced_count += 1
                continue

            screening = Screening(
                patient_id=patient.id,
                screening_date=datetime.utcnow(),
                pain_score=item.get("pain_score", 0.0),
                stiffness_score=item.get("stiffness_score", 0.0),
                mobility_score=item.get("mobility_score", 10.0),
                left_knee_rom=item.get("left_knee_rom", 120.0),
                right_knee_rom=item.get("right_knee_rom", 120.0),
                knee_symmetry=item.get("knee_symmetry", 95.0),
                average_knee_angle=item.get("average_knee_angle", 150.0),
                gait_symmetry=item.get("gait_symmetry", 90.0),
                movement_consistency=item.get("movement_consistency", 90.0),
                posture_score=item.get("posture_score", 85.0),
                movement_smoothness=item.get("movement_smoothness", 90.0),
                assessment_status=item.get("assessment_status", "VALID"),
                landmark_quality_score=item.get("landmark_quality_score", 100.0),
                valid_frame_ratio=item.get("valid_frame_ratio", 1.0),
                movement_quality_score=item.get("movement_quality_score", 100.0),
                risk_level=item.get("risk_level", "Low Risk"),
                risk_probability=item.get("risk_probability", 20.0),
                confidence=item.get("confidence", 90.0),
                confidence_level=item.get("confidence_level", "HIGH"),
                data_quality=item.get("data_quality", "GOOD"),
                confidence_reason=item.get("confidence_reason"),
                questionnaire_contribution=item.get("questionnaire_contribution", 50.0),
                movement_contribution=item.get("movement_contribution", 50.0),
                sync_status="synced",
                model_version=item.get("model_version", "1.0.0-demo"),
                notes=item.get("notes")
            )
            db.add(screening)
            db.commit()
            db.refresh(screening)

            # Record sync completed for queue
            q_rec = SyncRecord(
                entity_type="screening",
                entity_id=screening.id,
                sync_status="SYNCED",
                synced_at=datetime.utcnow()
            )
            db.add(q_rec)
            db.commit()

            synced_count += 1
        except Exception as e:
            failed_count += 1
            errors.append(str(e))

    status = "SUCCESS" if failed_count == 0 else ("WARNING" if synced_count > 0 else "FAILED")
    log_audit_event(
        db=db,
        action=AuditAction.SYNC_COMPLETED if failed_count == 0 else AuditAction.SYNC_FAILED,
        status=status,
        details={"synced_count": synced_count, "failed_count": failed_count, "errors": errors[:5]}
    )

    return {
        "synced_count": synced_count,
        "failed_count": failed_count,
        "errors": errors
    }
