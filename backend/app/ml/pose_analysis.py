import math
from typing import Dict, Any, Tuple, Optional

def calculate_angle_3points(
    a: Tuple[float, float],
    b: Tuple[float, float],
    c: Tuple[float, float]
) -> float:
    """
    Calculates the 2D planar angle at vertex b between vectors (a - b) and (c - b).
    Formula:
      u = a - b
      v = c - b
      angle = arccos((u . v) / (|u| * |v|))
    Returns angle in degrees [0.0, 180.0].
    """
    ba_x = a[0] - b[0]
    ba_y = a[1] - b[1]
    bc_x = c[0] - b[0]
    bc_y = c[1] - b[1]

    dot_product = (ba_x * bc_x) + (ba_y * bc_y)
    mag_ba = math.sqrt(ba_x * ba_x + ba_y * ba_y)
    mag_bc = math.sqrt(bc_x * bc_x + bc_y * bc_y)

    if mag_ba == 0.0 or mag_bc == 0.0:
        return 180.0

    cosine_angle = dot_product / (mag_ba * mag_bc)
    # Numerical clamping to avoid floating point domain errors for math.acos
    cosine_angle = max(-1.0, min(1.0, cosine_angle))
    angle_rad = math.acos(cosine_angle)
    return round(math.degrees(angle_rad), 2)

def calculate_knee_angles(landmarks: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
    """
    Computes left and right knee angles from Hip -> Knee -> Ankle landmarks.
    Expected landmark dictionary keys:
      - left_hip, left_knee, left_ankle
      - right_hip, right_knee, right_ankle
    """
    left_angle = 180.0
    right_angle = 180.0

    if all(k in landmarks for k in ["left_hip", "left_knee", "left_ankle"]):
        left_angle = calculate_angle_3points(
            landmarks["left_hip"],
            landmarks["left_knee"],
            landmarks["left_ankle"]
        )

    if all(k in landmarks for k in ["right_hip", "right_knee", "right_ankle"]):
        right_angle = calculate_angle_3points(
            landmarks["right_hip"],
            landmarks["right_knee"],
            landmarks["right_ankle"]
        )

    return {
        "left_knee_angle": left_angle,
        "right_knee_angle": right_angle
    }

def analyze_posture(landmarks: Dict[str, Tuple[float, float]]) -> Dict[str, Any]:
    """
    Analyzes body posture based on pose landmarks:
    - Shoulder horizontal alignment tilt
    - Hip horizontal alignment tilt
    - Torso vertical inclination
    - Lateral symmetry
    Returns posture metrics and a composite Posture Score (0 - 100).
    """
    posture_deductions = 0.0
    details = {}

    # 1. Shoulder Alignment
    if "left_shoulder" in landmarks and "right_shoulder" in landmarks:
        ls = landmarks["left_shoulder"]
        rs = landmarks["right_shoulder"]
        dy = abs(ls[1] - rs[1])
        dx = max(abs(ls[0] - rs[0]), 0.001)
        shoulder_tilt_deg = math.degrees(math.atan2(dy, dx))
        details["shoulder_tilt_deg"] = round(shoulder_tilt_deg, 2)
        # Normal shoulder tilt is < 3 deg
        if shoulder_tilt_deg > 3.0:
            posture_deductions += min(15.0, (shoulder_tilt_deg - 3.0) * 2.5)

    # 2. Hip Alignment
    if "left_hip" in landmarks and "right_hip" in landmarks:
        lh = landmarks["left_hip"]
        rh = landmarks["right_hip"]
        dy = abs(lh[1] - rh[1])
        dx = max(abs(lh[0] - rh[0]), 0.001)
        hip_tilt_deg = math.degrees(math.atan2(dy, dx))
        details["hip_tilt_deg"] = round(hip_tilt_deg, 2)
        # Normal pelvic tilt is < 3 deg
        if hip_tilt_deg > 3.0:
            posture_deductions += min(15.0, (hip_tilt_deg - 3.0) * 2.5)

    # 3. Torso Vertical Inclination
    if all(k in landmarks for k in ["left_shoulder", "right_shoulder", "left_hip", "right_hip"]):
        mid_shoulder_x = (landmarks["left_shoulder"][0] + landmarks["right_shoulder"][0]) / 2.0
        mid_shoulder_y = (landmarks["left_shoulder"][1] + landmarks["right_shoulder"][1]) / 2.0
        mid_hip_x = (landmarks["left_hip"][0] + landmarks["right_hip"][0]) / 2.0
        mid_hip_y = (landmarks["left_hip"][1] + landmarks["right_hip"][1]) / 2.0

        dx = abs(mid_shoulder_x - mid_hip_x)
        dy = max(abs(mid_shoulder_y - mid_hip_y), 0.001)
        torso_tilt_deg = math.degrees(math.atan2(dx, dy))
        details["torso_inclination_deg"] = round(torso_tilt_deg, 2)
        if torso_tilt_deg > 4.0:
            posture_deductions += min(20.0, (torso_tilt_deg - 4.0) * 3.0)

    posture_score = max(35.0, min(100.0, round(100.0 - posture_deductions, 1)))
    details["posture_score"] = posture_score
    details["posture_rating"] = (
        "Optimal" if posture_score >= 85 else
        "Acceptable" if posture_score >= 70 else
        "Mild Asymmetry" if posture_score >= 55 else "Significant Deviation"
    )
    return details
