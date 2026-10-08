import pytest
import numpy as np
import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.ml.gait_analysis import analyze_gait_time_series
from app.ml.pose_analysis import calculate_knee_angles, calculate_angle_3points, analyze_posture
from app.ml.inference import evaluate_screening_quality_gate

def test_pattern_a_normal_smooth_movement():
    """Pattern A: Normal smooth movement should yield stable ROM and high smoothness."""
    frames = []
    # 60 frames representing smooth sine wave flexion-extension cycle (170° down to 80° back to 170°)
    for i in range(60):
        t = i / 60.0
        angle = 125.0 + 45.0 * np.cos(2 * np.pi * t)
        frames.append({
            "timestamp": i * 33.3,
            "left_knee_angle": float(angle),
            "right_knee_angle": float(angle),
            "frame_valid": True
        })
    res = analyze_gait_time_series(frames)
    assert res["left_knee_rom"] >= 80.0
    assert res["knee_symmetry"] >= 90.0
    assert res["movement_smoothness"] >= 70.0
    assert res["gait_score"] >= 80.0

def test_pattern_b_slow_movement():
    """Pattern B: Slow deliberate movement across 120 frames."""
    frames = []
    for i in range(120):
        t = i / 120.0
        angle = 130.0 + 40.0 * np.cos(2 * np.pi * t)
        frames.append({
            "timestamp": i * 50.0,
            "left_knee_angle": float(angle),
            "right_knee_angle": float(angle),
            "frame_valid": True
        })
    res = analyze_gait_time_series(frames)
    assert res["left_knee_rom"] >= 70.0
    assert res["temporal_stability_score"] >= 75.0

def test_pattern_c_fast_movement():
    """Pattern C: Fast movement within plausible physiological velocity limits."""
    frames = []
    for i in range(30):
        t = i / 30.0
        angle = 125.0 + 40.0 * np.cos(4 * np.pi * t)
        frames.append({
            "timestamp": i * 33.3,
            "left_knee_angle": float(angle),
            "right_knee_angle": float(angle),
            "frame_valid": True
        })
    res = analyze_gait_time_series(frames)
    assert res["peak_left_velocity"] > 50.0
    assert res["left_knee_rom"] >= 60.0

def test_pattern_d_temporary_landmark_dropout():
    """Pattern D: Short temporary dropout (2 frames) smoothed/clamped cleanly."""
    frames = []
    for i in range(50):
        angle = 130.0 + 40.0 * np.cos(2 * np.pi * (i / 50.0))
        # 2 dropped frames with fallback values
        if i in [20, 21]:
            frames.append({
                "timestamp": i * 33.3,
                "left_knee_angle": 180.0,
                "right_knee_angle": 180.0,
                "frame_valid": False
            })
        else:
            frames.append({
                "timestamp": i * 33.3,
                "left_knee_angle": float(angle),
                "right_knee_angle": float(angle),
                "frame_valid": True
            })
    res = analyze_gait_time_series(frames)
    assert res["left_knee_rom"] >= 50.0
    assert res["movement_consistency"] >= 60.0

def test_pattern_e_noisy_jittery_landmarks():
    """Pattern E: Jittery noise spikes filtered by moving average without corrupting baseline."""
    frames = []
    np.random.seed(42)
    for i in range(60):
        base_angle = 120.0 + 40.0 * np.cos(2 * np.pi * (i / 60.0))
        noise = np.random.normal(0, 3.0)
        frames.append({
            "timestamp": i * 33.3,
            "left_knee_angle": float(np.clip(base_angle + noise, 30.0, 180.0)),
            "right_knee_angle": float(np.clip(base_angle + noise, 30.0, 180.0)),
            "frame_valid": True
        })
    res = analyze_gait_time_series(frames)
    assert 60.0 <= res["left_knee_rom"] <= 95.0
    assert res["knee_symmetry"] >= 85.0

def test_pattern_f_partial_leaving_frame_and_large_dropout():
    """Pattern F: Person partially leaves frame causing low valid frame ratio; Quality Gate flags REPEAT."""
    movement_summary = {
        'left_knee_rom': 60.0, 'right_knee_rom': 65.0, 'knee_symmetry': 85.0,
        'average_knee_angle': 120.0, 'gait_symmetry': 80.0, 'movement_consistency': 60.0,
        'posture_score': 65.0, 'hip_movement': 20.0, 'ankle_movement': 15.0,
        'movement_smoothness': 60.0,
        'landmark_quality_score': 42.0,   # Dropped out of view
        'valid_frame_ratio': 0.48,        # < 0.65 threshold
        'movement_quality_score': 50.0,
        'movement_duration': 8.0
    }
    questionnaire = {
        'knee_pain': 2, 'joint_stiffness': 1, 'walking_difficulty': 1,
        'stair_difficulty': 2, 'standing_difficulty': 1, 'knee_bending_difficulty': 2,
        'pain_increase_activity': 1, 'pain_scale': 5.0, 'mobility_scale': 6.0
    }
    qg = evaluate_screening_quality_gate(movement_summary, questionnaire)
    assert qg["assessment_quality"] == "POOR"
    assert qg["gate_decision"] == "REJECT_REPEAT_REQUIRED"
    assert qg["retest_recommended"] is True

def test_pattern_g_very_small_movement_excursion():
    """Pattern G: Person barely moves (ROM < 15°)."""
    frames = []
    for i in range(40):
        frames.append({
            "timestamp": i * 33.3,
            "left_knee_angle": 172.0 + np.sin(i * 0.2) * 2.0,
            "right_knee_angle": 171.0 + np.sin(i * 0.2) * 2.0,
            "frame_valid": True
        })
    res = analyze_gait_time_series(frames)
    # ROM is minimal
    assert res["left_knee_rom"] <= 15.0
    assert res["right_knee_rom"] <= 15.0

def test_pattern_h_clear_completed_movement():
    """Pattern H: Full flexion and return cycle detected correctly."""
    frames = []
    # Starts at 175° -> deep flexion at 80° -> returns to 170°
    for i in range(50):
        t = i / 50.0
        angle = 127.5 + 47.5 * np.cos(2 * np.pi * t)
        frames.append({
            "timestamp": i * 33.3,
            "left_knee_angle": float(angle),
            "right_knee_angle": float(angle),
            "frame_valid": True
        })
    res = analyze_gait_time_series(frames)
    assert res["left_knee_rom"] >= 80.0
    assert res["repetition_count"] >= 1

def test_pattern_i_asymmetric_left_right_rom():
    """Pattern I: Legitimate bilateral difference (left restricted to 65°, right 120°)."""
    frames = []
    for i in range(50):
        t = i / 50.0
        left_ang = 142.5 + 32.5 * np.cos(2 * np.pi * t)   # ROM ~ 65°
        right_ang = 115.0 + 60.0 * np.cos(2 * np.pi * t)  # ROM ~ 120°
        frames.append({
            "timestamp": i * 33.3,
            "left_knee_angle": float(left_ang),
            "right_knee_angle": float(right_ang),
            "frame_valid": True
        })
    res = analyze_gait_time_series(frames)
    assert res["rom_difference"] >= 45.0
    assert res["knee_symmetry"] < 70.0  # Asymmetry captured genuinely

def test_pattern_j_camera_noise_and_angle_verification():
    """Pattern J: Hip -> Knee -> Ankle geometry robustness."""
    # Hip at (0, 0), Knee at (0, 1), Ankle at (1, 1) -> exact 90 degrees
    hip = (0.0, 0.0)
    knee = (0.0, 1.0)
    ankle = (1.0, 1.0)
    ang = calculate_angle_3points(hip, knee, ankle)
    assert abs(ang - 90.0) < 0.1

    # Collinear hip -> knee -> ankle -> exact 180 degrees
    ankle_collinear = (0.0, 2.0)
    ang_straight = calculate_angle_3points(hip, knee, ankle_collinear)
    assert abs(ang_straight - 180.0) < 0.1

# =========================================================================
# DEDICATED INDEPENDENT LIMB & ANATOMICAL PRESERVATION TESTS (REQUIREMENT 9)
# =========================================================================

def test_left_leg_lift_independence():
    """Only left leg lifts; right leg remains stationary at ~175° standing angle."""
    frames = []
    for i in range(40):
        t = i / 40.0
        # Left leg actively flexes/lifts up to 85° and returns
        left_ang = 130.0 + 45.0 * np.cos(2 * np.pi * t)
        # Right leg remains standing firm
        right_ang = 175.0 + np.sin(i * 0.1) * 0.8
        frames.append({
            "timestamp": i * 33.3,
            "left_knee_angle": float(left_ang),
            "right_knee_angle": float(right_ang),
            "frame_valid": True
        })
    res = analyze_gait_time_series(frames)
    assert res["left_knee_rom"] >= 80.0
    assert res["right_knee_rom"] <= 8.0  # Right leg does NOT mirror left leg!
    assert res["rom_difference"] >= 70.0

def test_right_leg_lift_independence():
    """Only right leg lifts; left leg remains stationary at ~175° standing angle."""
    frames = []
    for i in range(40):
        t = i / 40.0
        # Right leg actively flexes/lifts up to 90° and returns
        right_ang = 132.5 + 42.5 * np.cos(2 * np.pi * t)
        # Left leg remains standing firm
        left_ang = 176.0 + np.cos(i * 0.1) * 0.5
        frames.append({
            "timestamp": i * 33.3,
            "left_knee_angle": float(left_ang),
            "right_knee_angle": float(right_ang),
            "frame_valid": True
        })
    res = analyze_gait_time_series(frames)
    assert res["right_knee_rom"] >= 75.0
    assert res["left_knee_rom"] <= 8.0  # Left leg does NOT mirror right leg!
    assert res["rom_difference"] >= 65.0

def test_left_leg_swing_trajectory():
    """Left leg undergoes forward-backward swing cycle; hip-knee-ankle geometry preserved."""
    frames = []
    for i in range(50):
        t = i / 50.0
        # Leg swing oscillation
        left_ang = 145.0 + 30.0 * np.sin(2 * np.pi * t)
        frames.append({
            "timestamp": i * 33.3,
            "left_knee_angle": float(left_ang),
            "right_knee_angle": 174.0,
            "frame_valid": True
        })
    res = analyze_gait_time_series(frames)
    assert res["left_knee_rom"] >= 50.0
    assert res["right_knee_rom"] <= 5.0
    assert res["peak_left_velocity"] > 40.0

def test_right_leg_swing_trajectory():
    """Right leg undergoes forward-backward swing cycle."""
    frames = []
    for i in range(50):
        t = i / 50.0
        right_ang = 140.0 + 35.0 * np.sin(2 * np.pi * t)
        frames.append({
            "timestamp": i * 33.3,
            "left_knee_angle": 175.0,
            "right_knee_angle": float(right_ang),
            "frame_valid": True
        })
    res = analyze_gait_time_series(frames)
    assert res["right_knee_rom"] >= 60.0
    assert res["left_knee_rom"] <= 5.0

def test_alternating_left_right_leg_movement():
    """Alternating legs: Left moves in first half, Right moves in second half."""
    frames = []
    for i in range(60):
        if i < 30:
            # First half: Left lifts and returns
            t = i / 30.0
            l_ang = 125.0 + 45.0 * np.cos(2 * np.pi * t)
            r_ang = 175.0
        else:
            # Second half: Right lifts and returns
            t = (i - 30) / 30.0
            l_ang = 175.0
            r_ang = 125.0 + 45.0 * np.cos(2 * np.pi * t)
        frames.append({
            "timestamp": i * 33.3,
            "left_knee_angle": float(l_ang),
            "right_knee_angle": float(r_ang),
            "frame_valid": True
        })
    res = analyze_gait_time_series(frames)
    assert res["left_knee_rom"] >= 75.0
    assert res["right_knee_rom"] >= 75.0
    assert abs(res["left_knee_rom"] - res["right_knee_rom"]) < 10.0
    assert res["knee_symmetry"] >= 88.0
