import sys
import os
import sqlite3
import json

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.ml.inference import evaluate_screening_quality_gate, calculate_confidence, predict_oa_risk, get_early_medical_guidance
from app.services.trajectory_service import calculate_longitudinal_trajectory

def run_all_tests():
    print("=====================================================================")
    print("RUNNING QUALITY-GATED, CONFIDENCE-AWARE SCREENING TEST SUITE (15 TESTS)")
    print("=====================================================================")
    passed = 0
    total = 15

    # Standard valid questionnaire
    valid_q = {
        'knee_pain': 3, 'joint_stiffness': 2, 'walking_difficulty': 2,
        'stair_difficulty': 3, 'standing_difficulty': 2, 'knee_bending_difficulty': 3,
        'pain_increase_activity': 2, 'pain_scale': 7.0, 'mobility_scale': 4.0
    }

    # Standard valid movement
    valid_m = {
        'left_knee_rom': 85.0, 'right_knee_rom': 110.0, 'knee_symmetry': 72.0,
        'average_knee_angle': 98.0, 'gait_symmetry': 70.0, 'movement_consistency': 68.0,
        'posture_score': 65.0, 'hip_movement': 25.0, 'ankle_movement': 18.0,
        'movement_smoothness': 65.0, 'landmark_quality_score': 95.0,
        'valid_frame_ratio': 0.95, 'movement_quality_score': 88.0,
        'movement_duration': 8.5
    }

    # 1. Good-quality assessment
    q_rep1 = evaluate_screening_quality_gate(valid_m, valid_q)
    assert q_rep1["assessment_quality"] == "GOOD", f"Expected GOOD, got {q_rep1['assessment_quality']}"
    assert q_rep1["gate_decision"] == "PROCEED"
    assert q_rep1["retest_recommended"] is False
    print("[PASS] Test 1 Passed: Good-quality assessment classified as GOOD and PROCEED")
    passed += 1

    # 2. Fair-quality assessment
    fair_m = dict(valid_m)
    fair_m["landmark_quality_score"] = 65.0  # Marginal landmark tracking
    fair_m["valid_frame_ratio"] = 0.75
    q_rep2 = evaluate_screening_quality_gate(fair_m, valid_q)
    assert q_rep2["assessment_quality"] == "FAIR", f"Expected FAIR, got {q_rep2['assessment_quality']}"
    assert q_rep2["gate_decision"] == "PROCEED_WITH_CAUTION"
    print("[PASS] Test 2 Passed: Fair-quality assessment classified as FAIR with PROCEED_WITH_CAUTION")
    passed += 1

    # 3. Poor-quality assessment
    poor_m = dict(valid_m)
    poor_m["landmark_quality_score"] = 35.0
    poor_m["valid_frame_ratio"] = 0.40
    q_rep3 = evaluate_screening_quality_gate(poor_m, valid_q)
    assert q_rep3["assessment_quality"] == "POOR", f"Expected POOR, got {q_rep3['assessment_quality']}"
    assert q_rep3["gate_decision"] == "REJECT_REPEAT_REQUIRED"
    assert q_rep3["retest_recommended"] is True
    assert "repeat" in q_rep3["reason"].lower() or "insufficient" in q_rep3["reason"].lower()
    print("[PASS] Test 3 Passed: Poor-quality assessment classified as POOR and REJECT_REPEAT_REQUIRED")
    passed += 1

    # 4. Missing landmarks / zero landmarks
    missing_lm_m = dict(valid_m)
    missing_lm_m["landmark_quality_score"] = 0.0
    missing_lm_m["valid_frame_ratio"] = 0.0
    q_rep4 = evaluate_screening_quality_gate(missing_lm_m, valid_q)
    assert q_rep4["camera_quality"] == "POOR"
    assert q_rep4["assessment_quality"] == "POOR"
    print("[PASS] Test 4 Passed: Missing landmarks correctly triggers POOR Camera & Assessment Quality")
    passed += 1

    # 5. Unstable landmarks / severe jitter
    jitter_m = dict(valid_m)
    jitter_m["temporal_stability_score"] = 25.0
    jitter_m["landmark_quality_score"] = 45.0
    q_rep5 = evaluate_screening_quality_gate(jitter_m, valid_q)
    assert q_rep5["camera_quality"] == "POOR" or q_rep5["movement_capture"] == "POOR"
    assert q_rep5["assessment_quality"] == "POOR"
    print("[PASS] Test 5 Passed: Unstable landmarks / low temporal stability triggers POOR quality")
    passed += 1

    # 6. Incomplete movement / aborted test (< 2.0 seconds)
    aborted_m = dict(valid_m)
    aborted_m["movement_duration"] = 1.2
    q_rep6 = evaluate_screening_quality_gate(aborted_m, valid_q)
    assert q_rep6["movement_capture"] == "POOR"
    assert q_rep6["assessment_quality"] == "POOR"
    assert "movement duration" in q_rep6["reason"].lower()
    print("[PASS] Test 6 Passed: Incomplete movement duration (<2s) correctly rejected")
    passed += 1

    # 7. Missing questionnaire information
    missing_q = {
        'knee_pain': 0, 'joint_stiffness': 0, 'walking_difficulty': 0,
        'stair_difficulty': 0, 'standing_difficulty': 0, 'knee_bending_difficulty': 0,
        'pain_increase_activity': 0, 'pain_scale': None, 'mobility_scale': None
    }
    q_rep7 = evaluate_screening_quality_gate(valid_m, missing_q)
    assert q_rep7["feature_completeness"] in ["FAIR", "POOR"]
    print("[PASS] Test 7 Passed: Missing questionnaire entries flagged in Feature Completeness")
    passed += 1

    # 8. Strong model probability margin
    # High separation between top class and second class
    conf8, conf_cat8, margin8, reason8 = calculate_confidence(
        class_probabilities=[0.92, 0.05, 0.03],
        data_quality="GOOD",
        feature_completeness=1.0,
        movement_reliability=0.95
    )
    assert conf_cat8 == "HIGH", f"Expected HIGH, got {conf_cat8}"
    assert margin8 >= 0.70
    print("[PASS] Test 8 Passed: Strong model probability margin produces HIGH confidence")
    passed += 1

    # 9. Weak model probability margin
    # Ambiguous probability distribution between top two classes
    conf9, conf_cat9, margin9, reason9 = calculate_confidence(
        class_probabilities=[0.38, 0.35, 0.27],
        data_quality="GOOD",
        feature_completeness=1.0,
        movement_reliability=0.90
    )
    assert conf_cat9 in ["MEDIUM", "LOW"], f"Expected MEDIUM/LOW, got {conf_cat9}"
    assert margin9 < 0.15
    print("[PASS] Test 9 Passed: Weak model probability margin reduces confidence classification")
    passed += 1

    # 10. Poor-quality result excluded from valid trajectory trend
    mock_history = [
        {
            "id": 101, "screening_date": "2026-01-01T10:00:00",
            "risk_level": "Low Risk", "risk_probability": 25.0,
            "confidence": 88.0, "confidence_level": "HIGH", "data_quality": "GOOD",
            "assessment_status": "VALID", "left_knee_rom": 130.0, "right_knee_rom": 128.0,
            "knee_symmetry": 96.0, "gait_symmetry": 92.0, "movement_smoothness": 90.0,
            "pain_score": 1.0, "mobility_score": 9.0
        },
        {
            "id": 102, "screening_date": "2026-02-01T10:00:00",
            "risk_level": "High Risk", "risk_probability": 85.0,
            "confidence": 35.0, "confidence_level": "LOW", "data_quality": "POOR",
            "assessment_status": "POOR_QUALITY_EXCLUDED", "left_knee_rom": 50.0, "right_knee_rom": 50.0,
            "knee_symmetry": 50.0, "gait_symmetry": 50.0, "movement_smoothness": 40.0,
            "pain_score": 8.0, "mobility_score": 2.0
        }
    ]
    traj = calculate_longitudinal_trajectory(mock_history)
    # The second point should be flagged as NOT included in trend calculation
    assert traj["trajectory"][1]["is_included_in_trend"] is False, "POOR screening should not be included in trend"
    assert traj["valid_sessions_count"] == 1
    print("[PASS] Test 10 Passed: Poor-quality result excluded from valid trajectory calculation")
    passed += 1

    # 11. Poor-quality result marked Inconclusive overall
    assert traj["overall_status"] == "Inconclusive", f"Expected Inconclusive, got {traj['overall_status']}"
    assert "insufficient" in traj["trajectory_summary"].lower() or "inconclusive" in traj["trajectory_summary"].lower()
    print("[PASS] Test 11 Passed: Poor-quality recent session marked trajectory status as Inconclusive")
    passed += 1

    # 12. Valid result included in trajectory
    mock_history_valid = [
        {
            "id": 201, "screening_date": "2026-01-01T10:00:00",
            "risk_level": "High Risk", "risk_probability": 78.0,
            "confidence": 85.0, "confidence_level": "HIGH", "data_quality": "GOOD",
            "assessment_status": "VALID", "left_knee_rom": 95.0, "right_knee_rom": 100.0,
            "knee_symmetry": 75.0, "gait_symmetry": 74.0, "movement_smoothness": 70.0,
            "pain_score": 7.0, "mobility_score": 3.0
        },
        {
            "id": 202, "screening_date": "2026-03-01T10:00:00",
            "risk_level": "Moderate Risk", "risk_probability": 50.0,
            "confidence": 82.0, "confidence_level": "HIGH", "data_quality": "GOOD",
            "assessment_status": "VALID", "left_knee_rom": 115.0, "right_knee_rom": 118.0,
            "knee_symmetry": 88.0, "gait_symmetry": 85.0, "movement_smoothness": 82.0,
            "pain_score": 4.0, "mobility_score": 6.0
        }
    ]
    traj_valid = calculate_longitudinal_trajectory(mock_history_valid)
    assert traj_valid["overall_status"] == "Improving", f"Expected Improving, got {traj_valid['overall_status']}"
    assert traj_valid["valid_sessions_count"] == 2
    assert all(pt["is_included_in_trend"] for pt in traj_valid["trajectory"])
    print("[PASS] Test 12 Passed: Valid results properly included in trajectory with Improving status")
    passed += 1

    # 13. Correct medical-evaluation guidance
    g_low = get_early_medical_guidance("Low Risk", "GOOD")
    g_mod = get_early_medical_guidance("Moderate Risk", "GOOD")
    g_high = get_early_medical_guidance("High Risk", "GOOD")
    g_poor = get_early_medical_guidance("High Risk", "POOR")

    assert "No significant OA-related risk markers" in g_low
    assert "OA-related risk markers were identified" in g_mod
    assert "Multiple OA-related risk markers were identified" in g_high
    assert "Reliable screening could not be completed" in g_poor
    print("[PASS] Test 13 Passed: Correct medical-evaluation guidance provided across risk & quality states")
    passed += 1

    # 14. Existing patients remain accessible
    db_path = os.path.join(backend_dir, "data", "oasense.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM patients")
    patient_count = cur.fetchone()[0]
    assert patient_count >= 34, f"Expected at least 34 patients, found {patient_count}"
    print(f"[PASS] Test 14 Passed: All {patient_count} patients remain accessible")
    passed += 1

    # 15. Existing screenings remain accessible
    cur.execute("SELECT COUNT(*) FROM screenings")
    screening_count = cur.fetchone()[0]
    conn.close()
    assert screening_count >= 26, f"Expected at least 26 screenings, found {screening_count}"
    print(f"[PASS] Test 15 Passed: All {screening_count} screenings remain accessible")
    passed += 1

    print("=====================================================================")
    print(f"ALL {passed}/{total} TESTS PASSED SUCCESSFULLY!")
    print("=====================================================================")

if __name__ == "__main__":
    run_all_tests()
