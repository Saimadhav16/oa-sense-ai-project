from typing import List, Dict, Any
from sqlalchemy.orm import Session
from ..models import Patient, Screening

def sync_batch_screenings(db: Session, offline_screenings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Synchronizes offline screening records uploaded by clients operating in low-connectivity environments.
    Updates sync_status to 'synced' and returns reconciliation summary.
    """
    synced_count = 0
    failed_count = 0
    errors = []

    for item in offline_screenings:
        try:
            patient_id = item.get("patient_id")
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                # If patient was also created offline with a temporary code
                p_code = item.get("patient_code")
                if p_code:
                    patient = db.query(Patient).filter(Patient.patient_code == p_code).first()
                if not patient:
                    failed_count += 1
                    errors.append(f"Patient ID {patient_id} / Code {p_code} not found in database.")
                    continue

            screening = Screening(
                patient_id=patient.id,
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
                risk_level=item.get("risk_level", "Low Risk"),
                risk_probability=item.get("risk_probability", 20.0),
                confidence=item.get("confidence", 90.0),
                questionnaire_contribution=item.get("questionnaire_contribution", 50.0),
                movement_contribution=item.get("movement_contribution", 50.0),
                sync_status="synced",
                model_version=item.get("model_version", "1.0.0-demo"),
                notes=item.get("notes")
            )
            db.add(screening)
            synced_count += 1
        except Exception as e:
            failed_count += 1
            errors.append(str(e))

    db.commit()
    return {
        "synced_count": synced_count,
        "failed_count": failed_count,
        "errors": errors
    }
