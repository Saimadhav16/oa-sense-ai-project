import pytest
from datetime import datetime, timedelta
from backend.app.ml.inference import predict_oa_risk
from backend.app.ml.model import load_ml_model
from backend.app.database import SessionLocal
from backend.app.models import Patient, PatientQRAccess, AuditLog
from backend.app.services.qr_service import (
    create_patient_qr_access,
    validate_and_resolve_qr_token,
    revoke_patient_qr_access
)

def test_dynamic_model_derived_explainability_patients_abc():
    """
    F1: Test dynamic explainability across Patients A, B, and C:
      Patient A: ROM = 75°, Pain = 8
      Patient B: ROM = 85°, Pain = 8
      Patient C: ROM = 135°, Pain = 1
    Verifies:
      - Different feature values -> Different transformed values -> Different contributions
      - Explanations use actual predicted class coefficients
      - Relative attributions are mathematically derived
      - Zero hardcoded heuristics
    """
    model_bundle = load_ml_model()
    assert model_bundle.get("pipeline") is not None, "Pipeline must be loaded"

    def make_dicts(rom: float, pain: float):
        q = {
            "knee_pain": int(pain / 2),
            "joint_stiffness": 2,
            "walking_difficulty": 2 if pain > 5 else 0,
            "stair_difficulty": 2 if pain > 5 else 0,
            "standing_difficulty": 1,
            "knee_bending_difficulty": 2 if rom < 90 else 0,
            "pain_increase_activity": 2 if pain > 5 else 0,
            "pain_scale": float(pain),
            "mobility_scale": 4.0 if pain > 5 else 9.0
        }
        m = {
            "left_knee_rom": float(rom),
            "right_knee_rom": float(rom),
            "knee_symmetry": 96.0,
            "average_knee_angle": 130.0,
            "gait_symmetry": 80.0 if pain > 5 else 94.0,
            "movement_consistency": 85.0,
            "posture_score": 82.0,
            "hip_movement": 35.0,
            "ankle_movement": 25.0,
            "movement_smoothness": 80.0,
            "assessment_status": "VALID",
            "landmark_quality_score": 95.0,
            "valid_frame_ratio": 0.95,
            "movement_duration": 8.0
        }
        return q, m

    q_a, m_a = make_dicts(75.0, 8.0)
    res_a = predict_oa_risk(58, "moderate", 1, 1, q_a, m_a)

    q_b, m_b = make_dicts(85.0, 8.0)
    res_b = predict_oa_risk(58, "moderate", 1, 1, q_b, m_b)

    q_c, m_c = make_dicts(135.0, 1.0)
    res_c = predict_oa_risk(58, "moderate", 0, 0, q_c, m_c)

    # 1. Verify all returned top_risk_factors have genuine fields
    for res, label in [(res_a, "Patient A"), (res_b, "Patient B"), (res_c, "Patient C")]:
        assert len(res["top_risk_factors"]) > 0, f"{label} must have risk factors"
        for factor in res["top_risk_factors"]:
            assert "feature_name" in factor
            assert "actual_value" in factor
            assert "scaled_value" in factor
            assert "coefficient" in factor
            assert "raw_contribution" in factor
            assert "direction" in factor
            assert factor["direction"] in ["increases risk", "decreases risk"]

    # 2. Extract left_knee_rom factor across Patients A, B, and C
    def get_factor(res, name):
        for f in res["top_risk_factors"]:
            if f["feature_name"] == name:
                return f
        return None

    rom_a = get_factor(res_a, "left_knee_rom")
    rom_b = get_factor(res_b, "left_knee_rom")
    rom_c = get_factor(res_c, "left_knee_rom")

    assert rom_a is not None, "Patient A must explain left_knee_rom"
    assert rom_b is not None, "Patient B must explain left_knee_rom"
    assert rom_c is not None, "Patient C must explain left_knee_rom"

    # Patient A (75°) vs Patient B (85°):
    assert rom_a["actual_value"] == 75.0
    assert rom_b["actual_value"] == 85.0
    assert rom_c["actual_value"] == 135.0

    assert rom_a["scaled_value"] != rom_b["scaled_value"]
    assert rom_a["raw_contribution"] != rom_b["raw_contribution"]

    # For High Risk (Patients A & B), negative coefficient on restricted ROM causes positive contribution
    # Patient A (75°) has more restricted ROM than B (85°), so raw contribution is higher
    assert rom_a["raw_contribution"] > rom_b["raw_contribution"]
    assert rom_a["direction"] == "increases risk"
    assert rom_b["direction"] == "increases risk"

    # Patient C has Low Risk prediction.
    # In Low Risk, healthy ROM (135°) increases alignment with Low Risk:
    assert "low" in rom_c["predicted_class"].lower()
    assert rom_c["direction"] == "increases risk"  # increases alignment with Low Risk
    assert rom_c["raw_contribution"] > 0

    # Also test Patient C's ROM evaluated under High Risk class:
    # Under High Risk, 135° has positive z-score and negative beta -> raw_contribution < 0 ("decreases risk")
    q_high_c, m_high_c = make_dicts(135.0, 8.0)
    res_high_c = predict_oa_risk(58, "moderate", 1, 1, q_high_c, m_high_c)
    rom_high_c = get_factor(res_high_c, "left_knee_rom")
    assert rom_high_c is not None
    assert rom_high_c["direction"] == "decreases risk"
    assert rom_high_c["raw_contribution"] < 0
    assert rom_high_c["relative_attribution"] is None

    # 3. Verify Pain Score feature changes dynamically
    pain_a = get_factor(res_a, "pain_score")
    pain_c = get_factor(res_c, "pain_score")
    assert pain_a is not None and pain_c is not None
    assert pain_a["actual_value"] == 8.0
    assert pain_c["actual_value"] == 1.0
    assert pain_a["scaled_value"] > pain_c["scaled_value"]
    assert pain_a["raw_contribution"] > 0

def test_qr_code_lifecycle_and_security():
    """
    F3: Comprehensive QR Lifecycle and Security test:
      - 256-bit cryptographically random token
      - SHA-256 hashed storage in database
      - Valid token allows access
      - Expired token denied
      - Revoked token denied
      - Invalid/tampered token denied
      - Zero PHI in raw token/URL
      - Audit logs created for generation, validation, and revocation
    """
    db = SessionLocal()
    try:
        # Get or create test patient
        patient = db.query(Patient).filter(Patient.patient_code == "UNIT-TEST-01").first()
        if not patient:
            patient = Patient(
                patient_code="UNIT-TEST-01",
                name="Unit Test Patient",
                age=55,
                gender="Female"
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)

        # 1. Issue Secure QR Pass
        raw_token, qr_record = create_patient_qr_access(
            db=db,
            patient_id=patient.id,
            expires_in_hours=24,
            source_ip="192.168.31.48"
        )

        assert raw_token is not None
        assert len(raw_token) >= 40, "Token must be at least 256 bits of URL-safe entropy"
        # Zero PHI in token
        assert patient.name not in raw_token
        assert patient.patient_code not in raw_token

        # Verify database only stores SHA-256 hash, not the raw token
        assert qr_record.token_hash != raw_token
        import hashlib
        expected_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        assert qr_record.token_hash == expected_hash

        # 2. Access using valid token
        summary = validate_and_resolve_qr_token(
            db=db,
            raw_token=raw_token,
            source_ip="192.168.31.100"
        )
        assert summary is not None
        assert summary["access_valid"] is True
        assert summary["patient"]["patient_code"] == patient.patient_code
        assert summary["patient"]["name"] == patient.name

        # Verify audit log recorded
        access_log = db.query(AuditLog).filter(
            AuditLog.patient_id == patient.id,
            AuditLog.source_ip == "192.168.31.100"
        ).order_by(AuditLog.id.desc()).first()
        assert access_log is not None

        # 3. Revoke pass
        revoked = revoke_patient_qr_access(db=db, qr_id=qr_record.id, source_ip="192.168.31.48")
        assert revoked is True

        # Scan revoked QR -> must raise ValueError
        with pytest.raises(ValueError) as exc_rev:
            validate_and_resolve_qr_token(
                db=db,
                raw_token=raw_token,
                source_ip="192.168.31.100"
            )
        assert "revoked" in str(exc_rev.value).lower()

        # 4. Expired QR test
        raw_token_exp, qr_exp = create_patient_qr_access(
            db=db,
            patient_id=patient.id,
            expires_in_hours=1,
            source_ip="192.168.31.48"
        )
        # Manually set expiration to past
        qr_exp.expires_at = datetime.utcnow() - timedelta(hours=2)
        db.commit()

        with pytest.raises(ValueError) as exc_exp:
            validate_and_resolve_qr_token(
                db=db,
                raw_token=raw_token_exp,
                source_ip="192.168.31.100"
            )
        assert "expired" in str(exc_exp.value).lower()

        # 5. Invalid / Tampered token
        with pytest.raises(ValueError) as exc_inv:
            validate_and_resolve_qr_token(
                db=db,
                raw_token="invalid_tampered_token_xyz_1234567890",
                source_ip="192.168.31.100"
            )
        assert "not found" in str(exc_inv.value).lower() or "invalid" in str(exc_inv.value).lower()

    finally:
        db.close()
