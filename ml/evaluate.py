"""
OA-Sense AI: Model Evaluation and Diagnostics
============================================================
Evaluates saved model artifact, computes detailed confusion matrices,
per-class classification metrics, and Explainable AI feature weights.
============================================================
"""

import os
import joblib
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

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

TARGET_COLUMN = "risk_level"

def run_diagnostics():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "saved_models", "oa_risk_model.joblib")
    dataset_path = os.path.join(base_dir, "dataset", "synthetic_oa_dataset.csv")

    if not os.path.exists(model_path):
        print("Model file not found. Please run train.py first.")
        return

    bundle = joblib.load(model_path)
    pipe = bundle["pipeline"]
    print(f"Loaded Model: {bundle.get('model_name', 'Unknown')} (v{bundle.get('version')})")

    from sklearn.model_selection import train_test_split
    df = pd.read_csv(dataset_path)
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    preds = pipe.predict(X_test)
    target_names = ["Low Risk", "Moderate Risk", "High Risk"]
    
    print("\nOverall Classification Report (Test Set):")
    print(classification_report(y_test, preds, target_names=target_names))

    print("Confusion Matrix (Test Set):")
    print(confusion_matrix(y_test, preds))

    print("\nTop 5 Explainable Risk Factors (Feature Importances):")
    sorted_importances = sorted(
        bundle.get("feature_importances", {}).items(),
        key=lambda item: item[1],
        reverse=True
    )
    for feat, imp in sorted_importances[:5]:
        print(f"  • {feat:<25}: {imp:.4f}")

if __name__ == "__main__":
    run_diagnostics()
