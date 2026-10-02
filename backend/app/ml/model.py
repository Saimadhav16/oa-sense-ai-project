import os
import joblib
from typing import Optional, Dict, Any

_CACHED_MODEL_BUNDLE: Optional[Dict[str, Any]] = None

def get_model_path() -> str:
    # First check backend/models/
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path_1 = os.path.join(base_dir, "models", "oa_risk_model.joblib")
    if os.path.exists(path_1):
        return path_1
    
    # Fallback to ml/saved_models/
    path_2 = os.path.abspath(os.path.join(base_dir, "..", "ml", "saved_models", "oa_risk_model.joblib"))
    if os.path.exists(path_2):
        return path_2
    
    return path_1

def load_ml_model() -> Dict[str, Any]:
    """Loads and caches the trained ML model bundle."""
    global _CACHED_MODEL_BUNDLE
    if _CACHED_MODEL_BUNDLE is not None:
        return _CACHED_MODEL_BUNDLE

    model_path = get_model_path()
    if os.path.exists(model_path):
        try:
            _CACHED_MODEL_BUNDLE = joblib.load(model_path)
            print(f"[ML] Successfully loaded model bundle from: {model_path}")
            return _CACHED_MODEL_BUNDLE
        except Exception as e:
            print(f"[ML WARNING] Failed to load joblib bundle: {e}. Using rule-based fallback.")
    else:
        print(f"[ML WARNING] Model file not found at {model_path}. Using rule-based fallback.")

    # Fallback mock bundle for resilience
    _CACHED_MODEL_BUNDLE = {
        "pipeline": None,
        "model_name": "FallbackHeuristicClassifier",
        "feature_importances": {
            "pain_score": 0.28,
            "mobility_score": 0.22,
            "gait_symmetry": 0.18,
            "left_knee_rom": 0.14,
            "knee_symmetry": 0.10,
            "posture_score": 0.08
        },
        "version": "1.0.0-fallback",
        "disclaimer": "DEMO DATA — NOT FOR CLINICAL USE."
    }
    return _CACHED_MODEL_BUNDLE
