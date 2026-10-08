import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..database import get_db
from ..models import Patient, Screening, MovementFrame, Report
from ..schemas import (
    ScreeningCreate,
    ScreeningResponse,
    QuestionnaireInput,
    QuestionnaireAnalysisResponse,
    MovementSummaryInput,
    PredictionRequest,
    PredictionResponse
)
from ..ml.gait_analysis import analyze_gait_time_series
from ..ml.inference import predict_oa_risk
from ..services.sync_service import sync_batch_screenings
from ..services.audit_service import log_audit_event, AuditAction

router = APIRouter(prefix="/api", tags=["Screenings & Analysis"])

@router.post("/analysis/questionnaire", response_model=QuestionnaireAnalysisResponse)
def analyze_questionnaire(q: QuestionnaireInput):
    """Analyzes 9-point OA questionnaire responses."""
    pain_score = round(float(q.pain_scale), 1)
    stiffness_score = round(float(q.joint_stiffness), 1)
    mobility_score = round(float(q.mobility_scale), 1)

    if pain_score >= 6.0 or (stiffness_score >= 3 and mobility_score <= 4.0):
        prelim = "Elevated Symptom Burden"
        interp = "Reported joint symptoms indicate substantial daily limitation and discomfort."
    elif pain_score >= 3.0 or stiffness_score >= 2:
        prelim = "Moderate Symptom Burden"
        interp = "Reported joint symptoms suggest mild-to-moderate discomfort during weight-bearing activities."
    else:
        prelim = "Low Symptom Burden"
        interp = "Self-reported pain and stiffness are minimal with preserved mobility."

    return {
        "pain_score": pain_score,
        "stiffness_score": stiffness_score,
        "mobility_score": mobility_score,
        "walking_difficulty": q.walking_difficulty,
        "stair_difficulty": q.stair_difficulty,
        "preliminary_symptom_risk": prelim,
        "interpretation": interp
    }

@router.post("/analysis/movement")
def analyze_movement(summary_in: MovementSummaryInput):
    """Extracts gait, symmetry, cadence, and smoothness metrics from movement telemetry."""
    frames_dict = [f.dict() for f in summary_in.frames] if summary_in.frames else []
    metrics = analyze_gait_time_series(frames_dict)
    
    if summary_in.left_knee_rom > 0:
        metrics["left_knee_rom"] = summary_in.left_knee_rom
    if summary_in.right_knee_rom > 0:
        metrics["right_knee_rom"] = summary_in.right_knee_rom
    if summary_in.knee_symmetry > 0:
        metrics["knee_symmetry"] = summary_in.knee_symmetry
    if summary_in.posture_score > 0:
        metrics["posture_score"] = summary_in.posture_score

    return metrics

@router.post("/analysis/predict", response_model=PredictionResponse)
def predict_screening_risk(req: PredictionRequest):
    """Runs ML inference on combined patient, questionnaire, and movement inputs."""
    if req.movement.assessment_status in ["REPEAT_REQUIRED", "INSUFFICIENT_DATA"]:
        detail_msg = req.movement.validation_message or f"Assessment quality status is {req.movement.assessment_status}. Please reposition and repeat camera movement capture."
        raise HTTPException(
            status_code=400,
            detail=f"Unreliable camera data blocked from ML inference: {detail_msg}"
        )

    result = predict_oa_risk(
        age=req.age,
        activity_level=req.activity_level,
        joint_injury=req.joint_injury,
        family_history=req.family_history,
        questionnaire_dict=req.questionnaire.dict(),
        movement_dict=req.movement.dict()
    )
    return result

@router.post("/screenings", response_model=ScreeningResponse)
def create_screening(scr_in: ScreeningCreate, request: Request = None, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == scr_in.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if scr_in.movement.assessment_status in ["REPEAT_REQUIRED", "INSUFFICIENT_DATA"]:
        detail_msg = scr_in.movement.validation_message or f"Assessment quality status is {scr_in.movement.assessment_status}. Please reposition and repeat camera movement capture."
        raise HTTPException(
            status_code=400,
            detail=f"Unreliable camera data blocked from screening creation: {detail_msg}"
        )

    q_dict = scr_in.questionnaire.dict()
    m_dict = scr_in.movement.dict()

    pred = predict_oa_risk(
        age=patient.age,
        activity_level=patient.activity_level or "Moderate",
        joint_injury=patient.joint_injury or 0,
        family_history=patient.family_history or 0,
        questionnaire_dict=q_dict,
        movement_dict=m_dict
    )

    screening = Screening(
        patient_id=patient.id,
        pain_score=scr_in.questionnaire.pain_scale,
        stiffness_score=float(scr_in.questionnaire.joint_stiffness),
        mobility_score=scr_in.questionnaire.mobility_scale,
        questionnaire_json=json.dumps(q_dict),
        left_knee_rom=scr_in.movement.left_knee_rom,
        right_knee_rom=scr_in.movement.right_knee_rom,
        knee_symmetry=scr_in.movement.knee_symmetry,
        average_knee_angle=scr_in.movement.average_knee_angle,
        gait_symmetry=scr_in.movement.gait_symmetry,
        movement_consistency=scr_in.movement.movement_consistency,
        posture_score=scr_in.movement.posture_score,
        hip_movement=scr_in.movement.hip_movement,
        ankle_movement=scr_in.movement.ankle_movement,
        movement_smoothness=scr_in.movement.movement_smoothness,
        assessment_status=pred.get("assessment_status", scr_in.movement.assessment_status or "VALID"),
        landmark_quality_score=scr_in.movement.landmark_quality_score or 100.0,
        valid_frame_ratio=scr_in.movement.valid_frame_ratio or 1.0,
        movement_quality_score=scr_in.movement.movement_quality_score or 100.0,
        validation_message=scr_in.movement.validation_message,
        min_left_knee_angle=scr_in.movement.min_left_knee_angle,
        max_left_knee_angle=scr_in.movement.max_left_knee_angle,
        mean_left_knee_angle=scr_in.movement.mean_left_knee_angle,
        median_left_knee_angle=scr_in.movement.median_left_knee_angle,
        min_right_knee_angle=scr_in.movement.min_right_knee_angle,
        max_right_knee_angle=scr_in.movement.max_right_knee_angle,
        mean_right_knee_angle=scr_in.movement.mean_right_knee_angle,
        median_right_knee_angle=scr_in.movement.median_right_knee_angle,
        rom_difference=scr_in.movement.rom_difference,
        peak_left_velocity=scr_in.movement.peak_left_velocity,
        peak_right_velocity=scr_in.movement.peak_right_velocity,
        movement_duration=scr_in.movement.movement_duration,
        repetition_count=scr_in.movement.repetition_count,
        movement_tests_json=json.dumps(scr_in.movement.movement_tests) if scr_in.movement.movement_tests else None,
        risk_level=pred["risk_level"],
        risk_probability=pred["risk_probability"],
        confidence=pred["confidence"],
        confidence_level=pred.get("confidence_level", "HIGH"),
        data_quality=pred.get("data_quality", "GOOD"),
        confidence_reason=pred.get("confidence_reason"),
        quality_report_json=json.dumps(pred.get("quality_report")) if pred.get("quality_report") else None,
        early_guidance=pred.get("early_guidance"),
        confidence_breakdown_json=json.dumps(pred.get("confidence_breakdown")) if pred.get("confidence_breakdown") else None,
        questionnaire_contribution=pred["questionnaire_contribution"],
        movement_contribution=pred["movement_contribution"],
        explainability_json=json.dumps(pred["top_risk_factors"]),
        model_version=pred["model_version"],
        model_name=pred.get("model_name", "LogisticRegression"),
        prediction_status=pred.get("prediction_status", "COMPLETED"),
        sync_status=scr_in.sync_status or "synced",
        notes=scr_in.notes
    )
    db.add(screening)
    db.commit()
    db.refresh(screening)

    # Save movement frames if provided
    if scr_in.movement.frames:
        for f in scr_in.movement.frames:
            mf = MovementFrame(
                screening_id=screening.id,
                movement_type=f.movement_type or "KNEE_FLEXION",
                timestamp=f.timestamp,
                left_knee_angle=f.left_knee_angle,
                right_knee_angle=f.right_knee_angle,
                hip_angle=f.hip_angle,
                posture_value=f.posture_value,
                frame_valid=f.frame_valid if f.frame_valid is not None else True,
                phase=f.phase
            )
            db.add(mf)
        db.commit()

    client_ip = request.client.host if (request and hasattr(request, "client") and request.client) else None
    log_audit_event(
        db=db,
        action=AuditAction.SCREENING_COMPLETED,
        patient_id=patient.id,
        assessment_id=screening.id,
        status="SUCCESS",
        source_ip=client_ip,
        details={
            "risk_level": screening.risk_level,
            "risk_probability": screening.risk_probability,
            "confidence_level": screening.confidence_level
        }
    )

    return {
        "id": screening.id,
        "patient_id": patient.id,
        "patient_name": patient.name,
        "patient_code": patient.patient_code,
        "screening_date": screening.screening_date,
        "pain_score": screening.pain_score,
        "stiffness_score": screening.stiffness_score,
        "mobility_score": screening.mobility_score,
        "left_knee_rom": screening.left_knee_rom,
        "right_knee_rom": screening.right_knee_rom,
        "knee_symmetry": screening.knee_symmetry,
        "average_knee_angle": screening.average_knee_angle,
        "gait_symmetry": screening.gait_symmetry,
        "movement_consistency": screening.movement_consistency,
        "posture_score": screening.posture_score,
        "movement_smoothness": screening.movement_smoothness,
        "assessment_status": screening.assessment_status,
        "landmark_quality_score": screening.landmark_quality_score,
        "valid_frame_ratio": screening.valid_frame_ratio,
        "movement_quality_score": screening.movement_quality_score,
        "validation_message": screening.validation_message,
        "min_left_knee_angle": screening.min_left_knee_angle,
        "max_left_knee_angle": screening.max_left_knee_angle,
        "mean_left_knee_angle": screening.mean_left_knee_angle,
        "median_left_knee_angle": screening.median_left_knee_angle,
        "min_right_knee_angle": screening.min_right_knee_angle,
        "max_right_knee_angle": screening.max_right_knee_angle,
        "mean_right_knee_angle": screening.mean_right_knee_angle,
        "median_right_knee_angle": screening.median_right_knee_angle,
        "rom_difference": screening.rom_difference,
        "peak_left_velocity": screening.peak_left_velocity,
        "peak_right_velocity": screening.peak_right_velocity,
        "movement_duration": screening.movement_duration,
        "repetition_count": screening.repetition_count,
        "movement_tests": json.loads(screening.movement_tests_json) if screening.movement_tests_json else None,
        "model_name": screening.model_name or "LogisticRegression",
        "prediction_status": screening.prediction_status or "COMPLETED",
        "risk_level": screening.risk_level,
        "risk_probability": screening.risk_probability,
        "confidence": screening.confidence,
        "confidence_level": screening.confidence_level or "HIGH",
        "data_quality": screening.data_quality or "GOOD",
        "confidence_reason": screening.confidence_reason,
        "confidence_breakdown": json.loads(screening.confidence_breakdown_json) if screening.confidence_breakdown_json else None,
        "quality_report": json.loads(screening.quality_report_json) if screening.quality_report_json else None,
        "early_guidance": screening.early_guidance,
        "questionnaire_contribution": screening.questionnaire_contribution,
        "movement_contribution": screening.movement_contribution,
        "top_risk_factors": json.loads(screening.explainability_json) if screening.explainability_json else [],
        "explainability_json": screening.explainability_json,
        "notes": screening.notes,
        "sync_status": screening.sync_status,
        "model_version": screening.model_version,
        "created_at": screening.created_at,
        "updated_at": screening.updated_at,
        "report_id": None
    }

@router.get("/screenings", response_model=List[ScreeningResponse])
def get_screenings(
    patient_id: Optional[int] = None,
    risk_level: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Screening)
    if patient_id:
        query = query.filter(Screening.patient_id == patient_id)
    if risk_level and risk_level.lower() != "all":
        query = query.filter(Screening.risk_level.ilike(f"%{risk_level}%"))

    screenings = query.order_by(desc(Screening.screening_date)).offset(skip).limit(limit).all()
    results = []
    for s in screenings:
        p = db.query(Patient).filter(Patient.id == s.patient_id).first()
        r = db.query(Report).filter(Report.screening_id == s.id).first()
        results.append({
            "id": s.id,
            "patient_id": s.patient_id,
            "patient_name": p.name if p else "Unknown",
            "patient_code": p.patient_code if p else "N/A",
            "screening_date": s.screening_date,
            "pain_score": s.pain_score,
            "stiffness_score": s.stiffness_score,
            "mobility_score": s.mobility_score,
            "left_knee_rom": s.left_knee_rom,
            "right_knee_rom": s.right_knee_rom,
            "knee_symmetry": s.knee_symmetry,
            "average_knee_angle": s.average_knee_angle,
            "gait_symmetry": s.gait_symmetry,
            "movement_consistency": s.movement_consistency,
            "posture_score": s.posture_score,
            "movement_smoothness": s.movement_smoothness,
            "assessment_status": s.assessment_status or "VALID",
            "landmark_quality_score": s.landmark_quality_score or 100.0,
            "valid_frame_ratio": s.valid_frame_ratio or 1.0,
            "movement_quality_score": s.movement_quality_score or 100.0,
            "validation_message": s.validation_message,
            "min_left_knee_angle": s.min_left_knee_angle,
            "max_left_knee_angle": s.max_left_knee_angle,
            "mean_left_knee_angle": s.mean_left_knee_angle,
            "median_left_knee_angle": s.median_left_knee_angle,
            "min_right_knee_angle": s.min_right_knee_angle,
            "max_right_knee_angle": s.max_right_knee_angle,
            "mean_right_knee_angle": s.mean_right_knee_angle,
            "median_right_knee_angle": s.median_right_knee_angle,
            "rom_difference": s.rom_difference,
            "peak_left_velocity": s.peak_left_velocity,
            "peak_right_velocity": s.peak_right_velocity,
            "movement_duration": s.movement_duration,
            "repetition_count": s.repetition_count,
            "movement_tests": json.loads(s.movement_tests_json) if s.movement_tests_json else None,
            "model_name": s.model_name or "LogisticRegression",
            "prediction_status": s.prediction_status or "COMPLETED",
            "risk_level": s.risk_level,
            "risk_probability": s.risk_probability,
            "confidence": s.confidence,
            "confidence_level": s.confidence_level or "HIGH",
            "data_quality": s.data_quality or "GOOD",
            "confidence_reason": s.confidence_reason,
            "confidence_breakdown": json.loads(s.confidence_breakdown_json) if s.confidence_breakdown_json else None,
            "quality_report": json.loads(s.quality_report_json) if s.quality_report_json else None,
            "early_guidance": s.early_guidance,
            "questionnaire_contribution": s.questionnaire_contribution,
            "movement_contribution": s.movement_contribution,
            "top_risk_factors": json.loads(s.explainability_json) if s.explainability_json else [],
            "explainability_json": s.explainability_json,
            "notes": s.notes,
            "sync_status": s.sync_status,
            "model_version": s.model_version,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
            "report_id": r.id if r else None
        })
    return results

@router.get("/screenings/{id}")
def get_screening_by_id(id: int, request: Request, db: Session = Depends(get_db)):
    s = db.query(Screening).filter(Screening.id == id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Screening not found")

    client_ip = request.client.host if request.client else None
    log_audit_event(
        db=db,
        action=AuditAction.ASSESSMENT_VIEWED,
        patient_id=s.patient_id,
        assessment_id=s.id,
        status="SUCCESS",
        source_ip=client_ip
    )

    p = db.query(Patient).filter(Patient.id == s.patient_id).first()
    frames = db.query(MovementFrame).filter(MovementFrame.screening_id == s.id).order_by(MovementFrame.timestamp).all()
    report = db.query(Report).filter(Report.screening_id == s.id).first()

    return {
        "screening": s,
        "patient": p,
        "report_id": report.id if report else None,
        "frames": [{"timestamp": f.timestamp, "left_knee_angle": f.left_knee_angle, "right_knee_angle": f.right_knee_angle} for f in frames]
    }

@router.post("/screenings/sync")
def sync_screenings_endpoint(batch: List[Dict[str, Any]], db: Session = Depends(get_db)):
    result = sync_batch_screenings(db, batch)
    return result
