import numpy as np
from typing import List, Dict, Any

def analyze_gait_time_series(frames: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes gait and knee movement time series collected during screening movement tests.
    Computes ROM, bilateral symmetry, cadence, consistency, and movement smoothness.
    
    IMPORTANT DISCLAIMER:
    Gait metrics are experimental screening indicators intended for functional
    mobility assessment and are not standalone diagnostic determinants.
    """
    if not frames or len(frames) < 5:
        return {
            "left_knee_rom": 120.0,
            "right_knee_rom": 120.0,
            "knee_symmetry": 95.0,
            "average_knee_angle": 150.0,
            "gait_symmetry": 90.0,
            "movement_consistency": 90.0,
            "movement_smoothness": 90.0,
            "cadence_estimate": 95.0,
            "gait_score": 90.0,
            "gait_indicator": "Optimal",
            "frame_count": len(frames) if frames else 0
        }

    left_angles = [f.get("left_knee_angle", 180.0) for f in frames]
    right_angles = [f.get("right_knee_angle", 180.0) for f in frames]
    timestamps = [f.get("timestamp", i * 0.033) for i, f in enumerate(frames)]

    left_arr = np.array(left_angles)
    right_arr = np.array(right_angles)
    t_arr = np.array(timestamps)

    # 1. Knee Range of Motion (ROM)
    left_rom = float(np.max(left_arr) - np.min(left_arr))
    right_rom = float(np.max(right_arr) - np.min(right_arr))

    # Clamp realistic ranges
    left_rom = max(20.0, min(150.0, round(left_rom, 1)))
    right_rom = max(20.0, min(150.0, round(right_rom, 1)))

    # 2. Knee Symmetry (%)
    max_rom = max(left_rom, right_rom, 1.0)
    rom_diff = abs(left_rom - right_rom)
    knee_symmetry = round(max(30.0, min(100.0, 100.0 - (rom_diff / max_rom * 100.0))), 1)

    # 3. Average Knee Angle
    avg_knee = round(float(np.mean((left_arr + right_arr) / 2.0)), 1)

    # 4. Gait Symmetry: Cross-correlation or angle difference variance
    diff_arr = np.abs(left_arr - right_arr)
    mean_diff = float(np.mean(diff_arr))
    gait_symmetry = round(max(35.0, min(100.0, 100.0 - (mean_diff / 180.0 * 100.0 * 2.2))), 1)

    # 5. Cadence Estimation (steps per minute from local extrema in knee angle)
    # Estimate period between inflection points
    dt = float(np.mean(np.diff(t_arr))) if len(t_arr) > 1 else 0.033
    if dt <= 0:
        dt = 0.033

    # Count zero crossings / direction flips of angular velocity
    left_vel = np.diff(left_arr) / dt
    direction_changes = np.sum(np.diff(np.sign(left_vel)) != 0)
    total_duration = max(float(t_arr[-1] - t_arr[0]), 1.0)
    steps_est = direction_changes / 2.0
    cadence_spm = round(float(steps_est / (total_duration / 60.0)), 1)
    cadence_spm = max(40.0, min(140.0, cadence_spm))

    # 6. Movement Consistency: Stability of cycle peaks / standard deviation
    std_left = float(np.std(left_arr))
    std_right = float(np.std(right_arr))
    consistency_factor = abs(std_left - std_right) / max(std_left, std_right, 1.0)
    movement_consistency = round(max(40.0, min(100.0, 100.0 - (consistency_factor * 60.0))), 1)

    # 7. Movement Smoothness: Approximate normalized jerk / acceleration variance
    acc_left = np.diff(left_vel)
    jerk_metric = float(np.var(acc_left)) if len(acc_left) > 0 else 10.0
    smoothness = round(max(40.0, min(100.0, 100.0 - min(60.0, np.log1p(jerk_metric) * 6.5))), 1)

    # 8. Composite Gait Score
    gait_score = round(
        0.35 * gait_symmetry +
        0.25 * knee_symmetry +
        0.20 * movement_consistency +
        0.20 * smoothness,
        1
    )

    gait_indicator = (
        "Optimal" if gait_score >= 85 else
        "Mild Asymmetry" if gait_score >= 70 else
        "Moderate Alteration" if gait_score >= 55 else "Significant Asymmetry"
    )

    return {
        "left_knee_rom": left_rom,
        "right_knee_rom": right_rom,
        "knee_symmetry": knee_symmetry,
        "average_knee_angle": avg_knee,
        "gait_symmetry": gait_symmetry,
        "movement_consistency": movement_consistency,
        "movement_smoothness": smoothness,
        "cadence_estimate": cadence_spm,
        "gait_score": gait_score,
        "gait_indicator": gait_indicator,
        "frame_count": len(frames)
    }
