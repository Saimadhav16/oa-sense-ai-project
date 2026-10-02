from typing import Dict, Any, List
import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "age",
    "activity_level",
    "joint_injury",
    "family_history",
    "pain_score",
    "stiffness_score",
    "mobility_score",
    "walking_difficulty",
    "stair_difficulty",
    "standing_difficulty",
    "knee_bending_difficulty",
    "pain_increase_activity",
    "left_knee_rom",
    "right_knee_rom",
    "knee_symmetry",
    "average_knee_angle",
    "gait_symmetry",
    "movement_consistency",
    "posture_score",
    "hip_movement",
    "ankle_movement",
    "movement_smoothness"
]

ACTIVITY_LEVEL_MAP = {
    "sedentary": 0,
    "light": 1,
    "moderate": 2,
    "active": 3,
    "very active": 3,
    "high": 3
}

def map_activity_level(level_str: Any) -> int:
    if isinstance(level_str, (int, float)):
        return int(np.clip(level_str, 0, 3))
    cleaned = str(level_str).strip().lower()
    return ACTIVITY_LEVEL_MAP.get(cleaned, 2)

def prepare_feature_dict(
    age: int,
    activity_level: Any,
    joint_injury: int,
    family_history: int,
    q_data: Dict[str, Any],
    m_data: Dict[str, Any]
) -> Dict[str, float]:
    """
    Transforms raw user, questionnaire, and movement inputs into a standardized feature dictionary.
    """
    return {
        "age": float(age),
        "activity_level": float(map_activity_level(activity_level)),
        "joint_injury": float(joint_injury or 0),
        "family_history": float(family_history or 0),
        "pain_score": float(q_data.get("pain_scale", q_data.get("pain_score", 0.0))),
        "stiffness_score": float(q_data.get("joint_stiffness", q_data.get("stiffness_score", 0.0))),
        "mobility_score": float(q_data.get("mobility_scale", q_data.get("mobility_score", 10.0))),
        "walking_difficulty": float(q_data.get("walking_difficulty", 0.0)),
        "stair_difficulty": float(q_data.get("stair_difficulty", 0.0)),
        "standing_difficulty": float(q_data.get("standing_difficulty", 0.0)),
        "knee_bending_difficulty": float(q_data.get("knee_bending_difficulty", 0.0)),
        "pain_increase_activity": float(q_data.get("pain_increase_activity", 0.0)),
        "left_knee_rom": float(m_data.get("left_knee_rom", 120.0)),
        "right_knee_rom": float(m_data.get("right_knee_rom", 120.0)),
        "knee_symmetry": float(m_data.get("knee_symmetry", 95.0)),
        "average_knee_angle": float(m_data.get("average_knee_angle", 150.0)),
        "gait_symmetry": float(m_data.get("gait_symmetry", 90.0)),
        "movement_consistency": float(m_data.get("movement_consistency", 90.0)),
        "posture_score": float(m_data.get("posture_score", 85.0)),
        "hip_movement": float(m_data.get("hip_movement", 40.0)),
        "ankle_movement": float(m_data.get("ankle_movement", 30.0)),
        "movement_smoothness": float(m_data.get("movement_smoothness", 90.0))
    }

def to_model_dataframe(feature_dict: Dict[str, float]) -> pd.DataFrame:
    """Converts feature dict to DataFrame in expected column order."""
    row = {col: feature_dict.get(col, 0.0) for col in FEATURE_COLUMNS}
    return pd.DataFrame([row])
