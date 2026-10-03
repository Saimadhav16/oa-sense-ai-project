"""
DEMO DATA GENERATOR — NOT FOR CLINICAL USE
------------------------------------------------------------
IMPORTANT MEDICAL DISCLAIMER:
This script generates synthetic data strictly for software development,
testing, and architecture validation purposes.
DO NOT claim or assume that this synthetic data represents clinical truth.
Never use predictions generated from this data for actual clinical diagnosis.
------------------------------------------------------------
"""

import os
import numpy as np
import pandas as pd

def generate_synthetic_dataset(n_samples: int = 2000, random_seed: int = 42) -> pd.DataFrame:
    np.random.seed(random_seed)
    
    # Generate age: bimodal/skewed towards older demographic where OA prevalence is higher
    ages = np.clip(np.random.normal(55, 13, n_samples).astype(int), 20, 88)
    
    # Activity level: 0=Sedentary, 1=Light, 2=Moderate, 3=Very Active
    activity_levels = np.random.choice([0, 1, 2, 3], size=n_samples, p=[0.25, 0.40, 0.25, 0.10])
    
    # Joint injury history (0 or 1)
    joint_injuries = np.random.binomial(1, 0.22, size=n_samples)
    family_histories = np.random.binomial(1, 0.30, size=n_samples)
    
    # Synthetic risk latent score (0.0 to 1.0)
    latent_risk = (
        (ages - 20) / 68.0 * 0.32 +
        (3 - activity_levels) / 3.0 * 0.10 +
        joint_injuries * 0.18 +
        family_histories * 0.15 +
        np.random.normal(0, 0.08, size=n_samples)
    )
    latent_risk = np.clip(latent_risk, 0.0, 1.0)
    
    # Discretize latent risk into 3 balanced classes: 0 = Low Risk, 1 = Moderate Risk, 2 = High Risk
    risk_levels = np.zeros(n_samples, dtype=int)
    threshold_mod = np.quantile(latent_risk, 0.33)
    threshold_high = np.quantile(latent_risk, 0.67)
    risk_levels[latent_risk >= threshold_mod] = 1
    risk_levels[latent_risk >= threshold_high] = 2
    
    # Questionnaire responses driven by latent risk + clinical noise
    pain_scores = np.clip(latent_risk * 9.5 + np.random.normal(0, 1.0, n_samples), 0, 10).round(1)
    stiffness_scores = np.clip(latent_risk * 4.0 + np.random.normal(0, 0.5, n_samples), 0, 4).round().astype(int)
    mobility_scores = np.clip((1.0 - latent_risk) * 9.5 + np.random.normal(0, 1.0, n_samples), 0, 10).round(1)
    
    walking_difficulties = np.clip(latent_risk * 4.0 + np.random.normal(0, 0.5, n_samples), 0, 4).round().astype(int)
    stair_difficulties = np.clip(latent_risk * 4.2 + np.random.normal(0, 0.5, n_samples), 0, 4).round().astype(int)
    standing_difficulties = np.clip(latent_risk * 3.8 + np.random.normal(0, 0.5, n_samples), 0, 4).round().astype(int)
    knee_bending_difficulties = np.clip(latent_risk * 4.0 + np.random.normal(0, 0.5, n_samples), 0, 4).round().astype(int)
    pain_increase_activity = np.clip(latent_risk * 4.0 + np.random.normal(0, 0.6, n_samples), 0, 4).round().astype(int)

    # Biomechanical Computer Vision features (Knee ROM, symmetry, gait, posture)
    base_rom = 140.0 - (latent_risk * 55.0)
    left_knee_rom = np.clip(base_rom + np.random.normal(0, 6.0, n_samples), 60.0, 150.0).round(1)
    
    rom_disparity = np.where(joint_injuries == 1, np.random.normal(12.0, 4.0, n_samples), np.random.normal(3.0, 2.0, n_samples))
    right_knee_rom = np.clip(base_rom - rom_disparity * np.random.choice([-1, 1], n_samples) + np.random.normal(0, 5.0, n_samples), 60.0, 150.0).round(1)
    
    knee_symmetry = np.clip(100.0 - (np.abs(left_knee_rom - right_knee_rom) / np.maximum(left_knee_rom, right_knee_rom) * 100.0), 40.0, 100.0).round(1)
    average_knee_angle = ((left_knee_rom + right_knee_rom) / 2.0).round(1)
    
    gait_symmetry = np.clip(95.0 - (latent_risk * 38.0) + np.random.normal(0, 5.0, n_samples), 35.0, 100.0).round(1)
    movement_consistency = np.clip(92.0 - (latent_risk * 32.0) + np.random.normal(0, 5.0, n_samples), 40.0, 100.0).round(1)
    
    posture_score = np.clip(90.0 - (latent_risk * 35.0) + np.random.normal(0, 5.0, n_samples), 40.0, 100.0).round(1)
    
    hip_movement = np.clip(45.0 - (latent_risk * 18.0) + np.random.normal(0, 3.0, n_samples), 15.0, 55.0).round(1)
    ankle_movement = np.clip(35.0 - (latent_risk * 14.0) + np.random.normal(0, 2.5, n_samples), 10.0, 45.0).round(1)
    movement_smoothness = np.clip(94.0 - (latent_risk * 36.0) + np.random.normal(0, 5.0, n_samples), 35.0, 100.0).round(1)

    df = pd.DataFrame({
        "age": ages,
        "activity_level": activity_levels,
        "joint_injury": joint_injuries,
        "family_history": family_histories,
        "pain_score": pain_scores,
        "stiffness_score": stiffness_scores,
        "mobility_score": mobility_scores,
        "walking_difficulty": walking_difficulties,
        "stair_difficulty": stair_difficulties,
        "standing_difficulty": standing_difficulties,
        "knee_bending_difficulty": knee_bending_difficulties,
        "pain_increase_activity": pain_increase_activity,
        "left_knee_rom": left_knee_rom,
        "right_knee_rom": right_knee_rom,
        "knee_symmetry": knee_symmetry,
        "average_knee_angle": average_knee_angle,
        "gait_symmetry": gait_symmetry,
        "movement_consistency": movement_consistency,
        "posture_score": posture_score,
        "hip_movement": hip_movement,
        "ankle_movement": ankle_movement,
        "movement_smoothness": movement_smoothness,
        "risk_level": risk_levels
    })
    
    return df

if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "synthetic_oa_dataset.csv")
    df = generate_synthetic_dataset(n_samples=2000)
    df.to_csv(out_path, index=False)
    print(f"[DEMO DATA] Generated {len(df)} synthetic samples at: {out_path}")
    print("Class distribution:")
    print(df["risk_level"].value_counts(normalize=True).rename({0: "0 (Low Risk)", 1: "1 (Moderate Risk)", 2: "2 (High Risk)"}))
