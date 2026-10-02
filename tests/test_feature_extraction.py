import pytest
from backend.app.ml.preprocessing import prepare_feature_dict, to_model_dataframe, map_activity_level
from backend.app.ml.feature_extraction import extract_features

def test_activity_level_mapping():
    assert map_activity_level("Sedentary") == 0
    assert map_activity_level("Light") == 1
    assert map_activity_level("Moderate") == 2
    assert map_activity_level("High") == 3
    assert map_activity_level("Active") == 3

def test_feature_extraction_pipeline():
    q_data = {
        "pain_scale": 6.5,
        "joint_stiffness": 3,
        "mobility_scale": 4.0,
        "walking_difficulty": 3,
        "stair_difficulty": 3,
        "standing_difficulty": 2,
        "knee_bending_difficulty": 3,
        "pain_increase_activity": 3
    }
    m_data = {
        "left_knee_rom": 85.0,
        "right_knee_rom": 120.0,
        "knee_symmetry": 70.8,
        "average_knee_angle": 102.5,
        "gait_symmetry": 68.0,
        "movement_consistency": 72.0,
        "posture_score": 75.0,
        "hip_movement": 32.0,
        "ankle_movement": 22.0,
        "movement_smoothness": 70.0
    }

    f_dict, df = extract_features(
        age=62,
        activity_level="Moderate",
        joint_injury=1,
        family_history=1,
        questionnaire_dict=q_data,
        movement_dict=m_data
    )

    assert f_dict["age"] == 62.0
    assert f_dict["joint_injury"] == 1.0
    assert f_dict["pain_score"] == 6.5
    assert f_dict["left_knee_rom"] == 85.0
    assert df.shape == (1, 22)
