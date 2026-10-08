import os
import sys
import unittest
import json

# Add backend directory to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from app.database import SessionLocal
from app.models import Patient, Screening, AuditLog, PatientQRAccess, SyncRecord
from app.ml.inference import predict_oa_risk
from app.services.trajectory_service import calculate_trajectory
from app.services.qr_service import create_patient_qr_access, validate_and_resolve_qr_token, revoke_patient_qr_access
from app.services.sync_service import get_sync_queue_status, retry_failed_sync_records
from app.services.report_service import generate_pdf_report

class TestOASenseAIExtensions(unittest.TestCase):

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_existing_patient_retrieval(self):
        """Test retrieving existing pre-seeded patient records."""
        patients = self.db.query(Patient).all()
        self.assertGreater(len(patients), 0, "Database should contain existing patients")
        first_patient = patients[0]
        self.assertIsNotNone(first_patient.patient_code)
        self.assertIsNotNone(first_patient.name)

    def test_02_existing_screening_retrieval(self):
        """Test retrieving existing screenings without schema corruption."""
        screenings = self.db.query(Screening).all()
        self.assertGreater(len(screenings), 0, "Database should contain existing screenings")
        first_s = screenings[0]
        self.assertIsNotNone(first_s.risk_level)

    def test_03_confidence_aware_ml_inference(self):
        """Test ML inference returns real confidence level, data quality, and calibration reason."""
        q_data = {
            "knee_pain": 3,
            "joint_stiffness": 2,
            "walking_difficulty": 2,
            "stair_difficulty": 2,
            "standing_difficulty": 1,
            "knee_bending_difficulty": 2,
            "pain_increase_activity": 2,
            "pain_scale": 6.0,
            "mobility_scale": 5.0
        }
        m_data = {
            "left_knee_rom": 92.0,
            "right_knee_rom": 115.0,
            "knee_symmetry": 80.0,
            "average_knee_angle": 120.0,
            "gait_symmetry": 78.0,
            "movement_consistency": 82.0,
            "posture_score": 75.0,
            "hip_movement": 35.0,
            "ankle_movement": 25.0,
            "movement_smoothness": 80.0,
            "assessment_status": "VALID",
            "landmark_quality_score": 90.0,
            "valid_frame_ratio": 0.95
        }
        res = predict_oa_risk(
            age=58,
            activity_level="Moderate",
            joint_injury=1,
            family_history=1,
            questionnaire_dict=q_data,
            movement_dict=m_data
        )

        self.assertIn(res["confidence_level"], ["HIGH", "MEDIUM", "LOW"])
        self.assertIn(res["data_quality"], ["GOOD", "FAIR", "POOR"])
        self.assertIsNotNone(res["confidence_reason"])
        self.assertIn("top_risk_factors", res)
        # Check traceable Observed vs Model Inference separation
        first_factor = res["top_risk_factors"][0]
        self.assertIn("observed", first_factor)
        self.assertIn("inference", first_factor)

    def test_04_secure_qr_generation_validation_revocation(self):
        """Test cryptographically secure random token, hashing, validation, and revocation."""
        patient = self.db.query(Patient).first()
        raw_token, qr_record = create_patient_qr_access(
            db=self.db,
            patient_id=patient.id,
            expires_in_hours=24,
            source_ip="127.0.0.1"
        )
        self.assertTrue(len(raw_token) > 20, "Token must be random high entropy string")
        self.assertNotEqual(raw_token, qr_record.token_hash, "Raw token must never be stored in db")

        # Validate token resolution
        summary = validate_and_resolve_qr_token(self.db, raw_token, source_ip="127.0.0.1")
        self.assertTrue(summary["access_valid"])
        self.assertEqual(summary["patient"]["name"], patient.name)

        # Audit log verification
        audit = self.db.query(AuditLog).filter(
            AuditLog.patient_id == patient.id,
            AuditLog.action == "QR_ACCESSED"
        ).first()
        self.assertIsNotNone(audit, "Audit event must be logged for QR access")

        # Test revocation
        revoke_success = revoke_patient_qr_access(self.db, qr_record.id, source_ip="127.0.0.1")
        self.assertTrue(revoke_success)

        # Attempting access with revoked token must fail with ValueError
        with self.assertRaises(ValueError):
            validate_and_resolve_qr_token(self.db, raw_token, source_ip="127.0.0.1")

    def test_05_longitudinal_trajectory_service(self):
        """Test risk-marker trajectory calculation across historical screenings."""
        patient = self.db.query(Patient).first()
        screenings = self.db.query(Screening).filter(Screening.patient_id == patient.id).all()
        trajectory = calculate_trajectory(screenings)
        self.assertIn(trajectory["status"], ["Stable", "Improving", "Worsening", "Inconclusive"])
        self.assertIsNotNone(trajectory["summary"])

    def test_06_pdf_report_generation(self):
        """Test PDF generation with confidence, data quality, and explainability sections."""
        patient = self.db.query(Patient).first()
        screening = self.db.query(Screening).filter(Screening.patient_id == patient.id).first()

        pdf_path = generate_pdf_report(
            patient_data={"name": patient.name, "patient_code": patient.patient_code, "age": patient.age, "gender": patient.gender},
            screening_data={"id": screening.id, "risk_level": screening.risk_level, "pain_score": screening.pain_score, "left_knee_rom": screening.left_knee_rom, "right_knee_rom": screening.right_knee_rom},
            prediction_data={
                "risk_level": screening.risk_level,
                "confidence_level": "HIGH",
                "data_quality": "GOOD",
                "confidence_reason": "High landmark tracking accuracy.",
                "top_risk_factors": [{"factor": "ROM Flexion", "status": "Alert", "observed": "Observed 92° flexion", "inference": "Model correlated with stiffness"}]
            }
        )
        self.assertTrue(os.path.exists(pdf_path), "PDF report file must exist on disk")

    def test_07_sync_queue_observability(self):
        """Test offline sync queue status retrieval and retry mechanism."""
        status = get_sync_queue_status(self.db)
        self.assertIn("pending", status)
        self.assertIn("synced", status)
        retry_res = retry_failed_sync_records(self.db)
        self.assertIn("retried_count", retry_res)

if __name__ == "__main__":
    unittest.main()
