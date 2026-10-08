import pytest
import numpy as np
from backend.app.ml.gait_analysis import analyze_gait_time_series

def test_time_series_kinematics_and_velocities():
    # Construct 60 frames representing ~2 seconds of cyclical knee flexion (60° to 170°)
    frames = []
    for i in range(60):
        t = i * 33.3  # ms (~30 FPS)
        # Periodic flexion wave
        angle = 115.0 + 55.0 * np.cos(i * 0.2)
        frames.append({
            "timestamp": t,
            "left_knee_angle": float(angle),
            "right_knee_angle": float(angle + 5.0 * np.sin(i * 0.1)),
            "frame_valid": True,
            "phase": "flexion" if np.sin(i * 0.2) > 0 else "extension"
        })

    result = analyze_gait_time_series(frames)

    # 1. Angle statistics
    assert "min_left_knee_angle" in result
    assert "max_left_knee_angle" in result
    assert "mean_left_knee_angle" in result
    assert "median_left_knee_angle" in result
    assert result["min_left_knee_angle"] < result["max_left_knee_angle"]
    assert 50.0 <= result["min_left_knee_angle"] <= 75.0
    assert 160.0 <= result["max_left_knee_angle"] <= 180.0

    # 2. ROM and bilateral difference
    assert result["left_knee_rom"] > 80.0
    assert result["rom_difference"] >= 0.0

    # 3. Angular velocity & duration
    assert result["peak_left_velocity"] > 10.0
    assert result["movement_duration"] > 1.5

    # 4. Temporal stability & continuity
    assert result["signal_continuity_score"] >= 80.0
    assert result["temporal_stability_score"] >= 70.0

def test_time_series_empty_and_short_fallback():
    # Empty frames
    empty_res = analyze_gait_time_series([])
    assert empty_res["frame_count"] == 0
    assert empty_res["left_knee_rom"] == 120.0

    # Under 5 frames fallback
    short_res = analyze_gait_time_series([
        {"timestamp": 0, "left_knee_angle": 170.0, "right_knee_angle": 170.0}
    ])
    assert short_res["frame_count"] == 1
