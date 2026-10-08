import pytest
from backend.app.ml.model import load_ml_model
from backend.app.ml.inference import predict_oa_risk

def test_load_ml_model():
    bundle = load_ml_model()
    assert bundle is not None
    assert "pipeline" in bundle
    assert "version" in bundle

def test_prediction_output_structure():
    q_data = {
        "knee_pain": 3,
        "joint_stiffness": 2,
        "walking_difficulty": 2,
        "stair_difficulty": 3,
        "standing_difficulty": 2,
        "knee_bending_difficulty": 2,
        "pain_increase_activity": 2,
        "pain_scale": 5.0,
        "mobility_scale": 6.0
    }
    m_data = {
        "left_knee_rom": 105.0,
        "right_knee_rom": 110.0,
        "knee_symmetry": 95.4,
        "average_knee_angle": 140.0,
        "gait_symmetry": 84.0,
        "movement_consistency": 82.0,
        "posture_score": 80.0,
        "hip_movement": 38.0,
        "ankle_movement": 28.0,
        "movement_smoothness": 82.0
    }

    res = predict_oa_risk(
        age=56,
        activity_level="Moderate",
        joint_injury=0,
        family_history=1,
        questionnaire_dict=q_data,
        movement_dict=m_data
    )

    assert res["risk_level"] in ["Low Risk", "Moderate Risk", "High Risk"]
    assert 0.0 <= res["risk_probability"] <= 100.0
    assert 0.0 <= res["confidence"] <= 100.0
    assert round(res["questionnaire_contribution"] + res["movement_contribution"], 1) == 100.0
    assert len(res["top_risk_factors"]) > 0
    assert len(res["recommendations"]) > 0
    assert "does NOT provide a definitive diagnosis of osteoarthritis" in res["disclaimer"]
