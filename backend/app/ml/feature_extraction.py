from typing import Dict, Any, Tuple
from .preprocessing import prepare_feature_dict, to_model_dataframe

def extract_features(
    age: int,
    activity_level: str,
    joint_injury: int,
    family_history: int,
    questionnaire_dict: Dict[str, Any],
    movement_dict: Dict[str, Any]
) -> Tuple[Dict[str, float], Any]:
    """
    Combines demographic, questionnaire, and computer-vision movement features.
    Returns:
      - Raw standardized feature dictionary
      - Model-ready pandas DataFrame
    """
    features = prepare_feature_dict(
        age=age,
        activity_level=activity_level,
        joint_injury=joint_injury,
        family_history=family_history,
        q_data=questionnaire_dict,
        m_data=movement_dict
    )
    df = to_model_dataframe(features)
    return features, df
