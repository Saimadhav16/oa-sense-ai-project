import os
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from ..models import Screening, Patient, Report
from ..services.report_service import generate_pdf_report

router = APIRouter(prefix="/api/reports", tags=["Reports"])

class ReportGenerateRequest(BaseModel):
    screening_id: int

@router.post("/generate")
def generate_report(req: ReportGenerateRequest, db: Session = Depends(get_db)):
    screening = db.query(Screening).filter(Screening.id == req.screening_id).first()
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    patient = db.query(Patient).filter(Patient.id == screening.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Associated patient not found")

    # Prepare data dictionaries
    patient_dict = {
        "id": patient.id,
        "patient_code": patient.patient_code,
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "occupation": patient.occupation,
        "activity_level": patient.activity_level
    }

    screening_dict = {
        "id": screening.id,
        "screening_date": screening.screening_date,
        "pain_score": screening.pain_score,
        "stiffness_score": screening.stiffness_score,
        "mobility_score": screening.mobility_score,
        "left_knee_rom": screening.left_knee_rom,
        "right_knee_rom": screening.right_knee_rom,
        "knee_symmetry": screening.knee_symmetry,
        "gait_symmetry": screening.gait_symmetry,
        "posture_score": screening.posture_score,
        "movement_smoothness": screening.movement_smoothness,
        "risk_level": screening.risk_level,
        "risk_probability": screening.risk_probability,
        "confidence": screening.confidence,
        "questionnaire_contribution": screening.questionnaire_contribution,
        "movement_contribution": screening.movement_contribution
    }

    top_factors = []
    if screening.explainability_json:
        try:
            top_factors = json.loads(screening.explainability_json)
        except Exception:
            pass

    prediction_dict = {
        "risk_level": screening.risk_level,
        "risk_probability": screening.risk_probability,
        "confidence": screening.confidence,
        "questionnaire_contribution": screening.questionnaire_contribution,
        "movement_contribution": screening.movement_contribution,
        "top_risk_factors": top_factors
    }

    # Generate PDF
    pdf_path = generate_pdf_report(
        patient_data=patient_dict,
        screening_data=screening_dict,
        prediction_data=prediction_dict
    )

    # Persist or update Report record
    existing_report = db.query(Report).filter(Report.screening_id == screening.id).first()
    if existing_report:
        existing_report.file_path = pdf_path
        report_record = existing_report
    else:
        report_record = Report(
            screening_id=screening.id,
            file_path=pdf_path
        )
        db.add(report_record)

    db.commit()
    db.refresh(report_record)

    return {
        "report_id": report_record.id,
        "screening_id": screening.id,
        "file_name": os.path.basename(pdf_path),
        "download_url": f"/api/reports/{report_record.id}"
    }

@router.get("/{id}")
def download_report(id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == id).first()
    if not report or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report PDF file not found")

    filename = os.path.basename(report.file_path)
    return FileResponse(
        path=report.file_path,
        media_type="application/pdf",
        filename=filename
    )
