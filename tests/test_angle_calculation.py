import math
import pytest
from backend.app.ml.pose_analysis import calculate_angle_3points, calculate_knee_angles, analyze_posture

def test_straight_line_angle():
    # Points along vertical line: (0, 2) -> (0, 1) -> (0, 0)
    angle = calculate_angle_3points((0.0, 2.0), (0.0, 1.0), (0.0, 0.0))
    assert math.isclose(angle, 180.0, abs_tol=0.1)

def test_right_angle():
    # Right angle at (0, 0): (0, 1) and (1, 0)
    angle = calculate_angle_3points((0.0, 1.0), (0.0, 0.0), (1.0, 0.0))
    assert math.isclose(angle, 90.0, abs_tol=0.1)

def test_acute_and_obtuse_angles():
    # 45 degrees
    angle_45 = calculate_angle_3points((1.0, 1.0), (0.0, 0.0), (1.0, 0.0))
    assert math.isclose(angle_45, 45.0, abs_tol=0.5)

    # 135 degrees
    angle_135 = calculate_angle_3points((-1.0, 1.0), (0.0, 0.0), (1.0, 0.0))
    assert math.isclose(angle_135, 135.0, abs_tol=0.5)

def test_calculate_knee_angles():
    landmarks = {
        "left_hip": (0.4, 0.4),
        "left_knee": (0.4, 0.6),
        "left_ankle": (0.4, 0.8),
        "right_hip": (0.6, 0.4),
        "right_knee": (0.6, 0.6),
        "right_ankle": (0.7, 0.7)  # flexed
    }
    angles = calculate_knee_angles(landmarks)
    assert "left_knee_angle" in angles
    assert "right_knee_angle" in angles
    assert math.isclose(angles["left_knee_angle"], 180.0, abs_tol=1.0)
    assert angles["right_knee_angle"] < 180.0

def test_analyze_posture():
    landmarks = {
        "left_shoulder": (0.4, 0.2),
        "right_shoulder": (0.6, 0.2),
        "left_hip": (0.4, 0.5),
        "right_hip": (0.6, 0.5)
    }
    posture = analyze_posture(landmarks)
    assert posture["posture_score"] >= 85.0
    assert posture["posture_rating"] == "Optimal"
