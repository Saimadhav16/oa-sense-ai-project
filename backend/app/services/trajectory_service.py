from typing import List, Dict, Any
from datetime import datetime
import json
from sqlalchemy.orm import Session
from ..models import Screening, Patient
from .audit_service import log_audit_event, AuditAction

class MockScreeningObj:
    def __init__(self, d: Dict[str, Any]):
        for k, v in d.items():
            setattr(self, k, v)
        if not hasattr(self, "created_at"):
            self.created_at = datetime.utcnow()
        if isinstance(getattr(self, "screening_date", None), str):
            try:
                self.screening_date = datetime.fromisoformat(self.screening_date.replace("Z", ""))
            except Exception:
                self.screening_date = self.created_at

def calculate_longitudinal_trajectory(screenings_list: List[Any]) -> Dict[str, Any]:
    """Adapter function supporting list of dictionaries or ORM objects."""
    objs = []
    for s in screenings_list:
        if isinstance(s, dict):
            objs.append(MockScreeningObj(s))
        else:
            objs.append(s)
    res = calculate_trajectory(objs)
    # Provide alias keys for frontend & test convenience
    res["overall_status"] = res["status"]
    res["trajectory_summary"] = res["summary"]
    res["trajectory"] = res["trajectory_points"]
    return res

def calculate_trajectory(screenings: List[Screening]) -> Dict[str, Any]:
    """
    Computes transparent, longitudinal risk-marker trajectory across screening sessions.
    
    SAFETY & MEDICAL NOTICE:
    This algorithm does NOT predict future development of Osteoarthritis.
    It compares repeated preliminary screening markers over time.

    LONGITUDINAL SAFETY RULES:
    1. Only include assessments in valid trajectory computation if:
       - assessment_status is 'VALID' or 'LIMITED_QUALITY'
       - data_quality is 'GOOD' or 'FAIR'
       - prediction_status is 'COMPLETED'
    2. Assessments with data_quality == 'POOR' or assessment_status in ['REPEAT_REQUIRED', 'INSUFFICIENT_DATA', 'REJECTED_QUALITY_GATE']
       must NEVER be treated as equivalent to valid screenings.
    3. If the latest screening or all screenings are POOR:
       - Trajectory status is marked 'Inconclusive'
       - Trajectory summary explains: 'Latest screening session had insufficient assessment quality and was excluded from comparative trajectory analysis.'
       - Does NOT classify as 'Improving' or 'Worsening'.
    """
    if not screenings or len(screenings) == 0:
        return {
            "status": "Inconclusive",
            "summary": "No screening history recorded.",
            "trajectory_points": [],
            "comparison": None,
            "valid_sessions_count": 0,
            "excluded_sessions_count": 0
        }

    # Sort chronological (oldest to newest)
    sorted_sessions = sorted(screenings, key=lambda s: s.screening_date or s.created_at)

    trajectory_points = []
    valid_sessions: List[Screening] = []
    excluded_sessions: List[Screening] = []

    for idx, s in enumerate(sorted_sessions, start=1):
        is_poor = (
            (s.data_quality and s.data_quality.upper() == "POOR") or
            (s.assessment_status and s.assessment_status.upper() in ["REPEAT_REQUIRED", "INSUFFICIENT_DATA", "REJECTED_QUALITY_GATE"]) or
            (s.risk_level and "insufficient" in s.risk_level.lower())
        )

        point_entry = {
            "session_number": idx,
            "screening_id": s.id,
            "screening_date": (s.screening_date or s.created_at).isoformat(),
            "risk_level": s.risk_level,
            "risk_probability": round(s.risk_probability, 1) if s.risk_probability else 0.0,
            "confidence": round(s.confidence, 1) if s.confidence else 0.0,
            "confidence_level": s.confidence_level or "HIGH",
            "data_quality": s.data_quality or "GOOD",
            "assessment_status": s.assessment_status or "VALID",
            "is_included_in_trend": not is_poor,
            "left_knee_rom": round(s.left_knee_rom, 1) if s.left_knee_rom else 0.0,
            "right_knee_rom": round(s.right_knee_rom, 1) if s.right_knee_rom else 0.0,
            "knee_symmetry": round(s.knee_symmetry, 1) if s.knee_symmetry else 100.0,
            "gait_symmetry": round(s.gait_symmetry, 1) if s.gait_symmetry else 100.0,
            "movement_smoothness": round(s.movement_smoothness, 1) if s.movement_smoothness else 100.0,
            "pain_score": round(s.pain_score, 1) if s.pain_score else 0.0,
            "mobility_score": round(s.mobility_score, 1) if s.mobility_score else 10.0
        }
        trajectory_points.append(point_entry)

        if is_poor:
            excluded_sessions.append(s)
        else:
            valid_sessions.append(s)

    # If no valid sessions meet the quality threshold
    if len(valid_sessions) == 0:
        return {
            "status": "Inconclusive",
            "summary": "Assessment quality insufficient across recorded sessions. No valid baseline exists for longitudinal comparison.",
            "trajectory_points": trajectory_points,
            "comparison": None,
            "valid_sessions_count": 0,
            "excluded_sessions_count": len(excluded_sessions)
        }

    # If latest session is poor quality, mark current trend status inconclusive
    latest_overall = sorted_sessions[-1]
    if latest_overall in excluded_sessions:
        return {
            "status": "Inconclusive",
            "summary": (
                "The latest screening session had insufficient assessment quality and was excluded from comparative trend analysis. "
                "Please repeat the movement assessment with clear camera visibility to update trajectory tracking."
            ),
            "trajectory_points": trajectory_points,
            "comparison": {
                "sessions_compared": len(valid_sessions),
                "latest_valid_risk": valid_sessions[-1].risk_level,
                "latest_status": "EXCLUDED_INSUFFICIENT_QUALITY"
            },
            "valid_sessions_count": len(valid_sessions),
            "excluded_sessions_count": len(excluded_sessions)
        }

    # Only single valid session
    if len(valid_sessions) < 2:
        latest = valid_sessions[0]
        return {
            "status": "Stable",
            "summary": "Baseline screening established with valid data quality. Further screenings will establish longitudinal trajectory.",
            "trajectory_points": trajectory_points,
            "comparison": {
                "sessions_compared": 1,
                "latest_risk": latest.risk_level,
                "rom_change": 0.0,
                "pain_change": 0.0,
                "symmetry_change": 0.0
            },
            "valid_sessions_count": 1,
            "excluded_sessions_count": len(excluded_sessions)
        }

    # Compare last two VALID sessions
    prev = valid_sessions[-2]
    curr = valid_sessions[-1]

    curr_rom_avg = (curr.left_knee_rom + curr.right_knee_rom) / 2.0
    prev_rom_avg = (prev.left_knee_rom + prev.right_knee_rom) / 2.0
    rom_diff = round(curr_rom_avg - prev_rom_avg, 1)

    curr_sym = (curr.knee_symmetry + curr.gait_symmetry) / 2.0
    prev_sym = (prev.knee_symmetry + prev.gait_symmetry) / 2.0
    sym_diff = round(curr_sym - prev_sym, 1)

    pain_diff = round(curr.pain_score - prev.pain_score, 1)
    mobility_diff = round(curr.mobility_score - prev.mobility_score, 1)
    prob_diff = round(curr.risk_probability - prev.risk_probability, 1)

    risk_rank = {"Low Risk": 0, "Moderate Risk": 1, "High Risk": 2}
    curr_rank = risk_rank.get(curr.risk_level, 1)
    prev_rank = risk_rank.get(prev.risk_level, 1)

    if (rom_diff >= 5.0 or sym_diff >= 5.0 or pain_diff <= -1.5) and prob_diff <= 5.0 and curr_rank <= prev_rank:
        status = "Improving"
        summary = (
            "The latest valid assessment shows improved movement-related indicators and joint mobility "
            f"compared with the previous assessment (average ROM changed by {rom_diff:+}°, pain changed by {pain_diff:+} pts)."
        )
    elif (rom_diff <= -5.0 or sym_diff <= -5.0 or pain_diff >= 1.5 or prob_diff >= 12.0) or curr_rank > prev_rank:
        status = "Worsening"
        summary = (
            "OA-related screening markers have increased compared with the previous assessment. "
            f"Observed changes include {abs(rom_diff)}° ROM reduction or increased symptom indicators."
        )
    else:
        status = "Stable"
        summary = "Screening markers remain relatively stable compared to the prior screening session."

    return {
        "status": status,
        "summary": summary,
        "trajectory_points": trajectory_points,
        "comparison": {
            "sessions_compared": len(valid_sessions),
            "latest_risk": curr.risk_level,
            "previous_risk": prev.risk_level,
            "rom_change": rom_diff,
            "pain_change": pain_diff,
            "mobility_change": mobility_diff,
            "symmetry_change": sym_diff,
            "probability_change": prob_diff
        },
        "valid_sessions_count": len(valid_sessions),
        "excluded_sessions_count": len(excluded_sessions)
    }
