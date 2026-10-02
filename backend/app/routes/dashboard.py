import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from ..database import get_db
from ..models import Patient, Screening, Report
from ..schemas import DashboardStatistics

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/statistics", response_model=DashboardStatistics)
def get_dashboard_statistics(db: Session = Depends(get_db)):
    total_patients = db.query(func.count(Patient.id)).scalar() or 0

    today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    screenings_today = db.query(func.count(Screening.id)).filter(Screening.screening_date >= today_start).scalar() or 0

    high_risk_cases = db.query(func.count(Screening.id)).filter(Screening.risk_level.ilike("%High%")).scalar() or 0
    moderate_risk_cases = db.query(func.count(Screening.id)).filter(Screening.risk_level.ilike("%Moderate%")).scalar() or 0
    low_risk_cases = db.query(func.count(Screening.id)).filter(Screening.risk_level.ilike("%Low%")).scalar() or 0

    # Recent screening activities with patient name
    recent_screenings = db.query(Screening).order_by(desc(Screening.screening_date)).limit(8).all()
    recent_activity = []
    for s in recent_screenings:
        patient = db.query(Patient).filter(Patient.id == s.patient_id).first()
        recent_activity.append({
            "screening_id": s.id,
            "patient_id": s.patient_id,
            "patient_name": patient.name if patient else "Unknown",
            "patient_code": patient.patient_code if patient else "N/A",
            "age": patient.age if patient else 0,
            "risk_level": s.risk_level,
            "risk_probability": s.risk_probability,
            "pain_score": s.pain_score,
            "knee_symmetry": s.knee_symmetry,
            "screening_date": s.screening_date.isoformat()
        })

    return {
        "total_patients": total_patients,
        "screenings_today": screenings_today,
        "high_risk_cases": high_risk_cases,
        "moderate_risk_cases": moderate_risk_cases,
        "low_risk_cases": low_risk_cases,
        "risk_distribution": {
            "Low Risk": low_risk_cases,
            "Moderate Risk": moderate_risk_cases,
            "High Risk": high_risk_cases
        },
        "recent_activity": recent_activity
    }
