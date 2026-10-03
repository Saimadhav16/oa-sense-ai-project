"""
OA-Sense AI: Model Training Pipeline
Trains baseline and tree-based classifiers for OA Risk Screening.
============================================================
IMPORTANT MEDICAL DISCLAIMER:
This pipeline is trained on synthetic/demonstration data for architecture
validation. It is NOT validated for clinical diagnosis.
============================================================
"""

import os
import shutil
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix
)
from xgboost import XGBClassifier

# Import dataset generator
from dataset.generate_demo_data import generate_synthetic_dataset

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

def train_and_evaluate():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(base_dir, "dataset", "synthetic_oa_dataset.csv")
    
    if not os.path.exists(dataset_path):
        print("Generating synthetic demo dataset...")
        df = generate_synthetic_dataset(n_samples=2500)
        df.to_csv(dataset_path, index=False)
    else:
        df = pd.read_csv(dataset_path)

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    models = {
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42),
        "RandomForest": RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42),
        "XGBoost": XGBClassifier(n_estimators=120, max_depth=5, learning_rate=0.08, random_state=42)
    }

    results = {}
    fitted_pipelines = {}

    print("============================================================")
    print("OA-Sense AI: Training Risk Classification Models (DEMO MODE)")
    print("============================================================")

    for name, clf in models.items():
        pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("classifier", clf)
        ])

        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        y_proba = pipe.predict_proba(X_test)

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, average="weighted")
        rec = recall_score(y_test, y_pred, average="weighted")
        f1 = f1_score(y_test, y_pred, average="weighted")
        try:
            auc = roc_auc_score(y_test, y_proba, multi_class="ovr")
        except Exception:
            auc = 0.0

        results[name] = {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "roc_auc": auc
        }
        fitted_pipelines[name] = pipe

        print(f"\n--- Model: {name} ---")
        print(f"Accuracy:  {acc:.4f}")
        print(f"Precision: {prec:.4f}")
        print(f"Recall:    {rec:.4f}")
        print(f"F1 Score:  {f1:.4f}")
        print(f"ROC-AUC:   {auc:.4f}")
        print("Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

    # Select best model based on F1 Score
    best_model_name = max(results, key=lambda k: results[k]["f1"])
    best_pipe = fitted_pipelines[best_model_name]
    print(f"\n>> Selected Best Model: {best_model_name} (F1 = {results[best_model_name]['f1']:.4f})")

    # Extract feature importances if available
    classifier_step = best_pipe.named_steps["classifier"]
    feature_importances = {}
    if hasattr(classifier_step, "feature_importances_"):
        raw_importances = classifier_step.feature_importances_
        feature_importances = {feat: float(imp) for feat, imp in zip(FEATURE_COLUMNS, raw_importances)}
    elif hasattr(classifier_step, "coef_"):
        avg_coef = np.mean(np.abs(classifier_step.coef_), axis=0)
        feature_importances = {feat: float(imp) for feat, imp in zip(FEATURE_COLUMNS, avg_coef)}

    # Package model metadata
    model_bundle = {
        "pipeline": best_pipe,
        "model_name": best_model_name,
        "feature_names": FEATURE_COLUMNS,
        "feature_importances": feature_importances,
        "metrics": results[best_model_name],
        "version": "1.0.0-demo",
        "disclaimer": "DEMO DATA — NOT FOR CLINICAL USE. Research prototype only."
    }

    # Save to ml/saved_models/
    saved_models_dir = os.path.join(base_dir, "saved_models")
    os.makedirs(saved_models_dir, exist_ok=True)
    target_joblib = os.path.join(saved_models_dir, "oa_risk_model.joblib")
    joblib.dump(model_bundle, target_joblib)
    print(f"Model saved to: {target_joblib}")

    # Copy to backend/models/
    backend_models_dir = os.path.abspath(os.path.join(base_dir, "..", "backend", "models"))
    os.makedirs(backend_models_dir, exist_ok=True)
    backend_target = os.path.join(backend_models_dir, "oa_risk_model.joblib")
    shutil.copyfile(target_joblib, backend_target)
    print(f"Model mirrored to backend at: {backend_target}")

    return model_bundle

if __name__ == "__main__":
    train_and_evaluate()
