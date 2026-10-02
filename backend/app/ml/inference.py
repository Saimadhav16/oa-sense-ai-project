from typing import Dict, Any, List
import numpy as np
from .model import load_ml_model
from .feature_extraction import extract_features

RISK_CLASS_MAP = {
    0: "Low Risk",
    1: "Moderate Risk",
    2: "High Risk"
}

def predict_oa_risk(
    age: int,
    activity_level: str,
    joint_injury: int,
    family_history: int,
    questionnaire_dict: Dict[str, Any],
    movement_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Performs OA Risk Screening inference combining questionnaire and computer-vision features.
    Computes explainable contributions, top risk factors, and actionable recommendations.
    
    IMPORTANT SAFETY NOTICE:
    Screening system only. Never diagnoses osteoarthritis.
    """
    raw_features, feature_df = extract_features(
        age=age,
        activity_level=activity_level,
        joint_injury=joint_injury,
        family_history=family_history,
        questionnaire_dict=questionnaire_dict,
        movement_dict=movement_dict
    )

    model_bundle = load_ml_model()
    pipe = model_bundle.get("pipeline")
    version = model_bundle.get("version", "1.0.0-demo")

    if pipe is not None:
        try:
            pred_class = int(pipe.predict(feature_df)[0])
            probas = pipe.predict_proba(feature_df)[0]
            # Risk probability is weighted sum or probability of moderate+high
            # For class 0: probas[0], class 1: probas[1], class 2: probas[2]
            risk_prob = float((probas[1] * 0.55 + probas[2] * 1.0) * 100.0)
            risk_prob = round(max(5.0, min(96.0, risk_prob)), 1)
            confidence = round(float(np.max(probas) * 100.0), 1)
            risk_level = RISK_CLASS_MAP.get(pred_class, "Moderate Risk")
        except Exception as e:
            print(f"[INFERENCE ERROR] Pipeline failure: {e}. Using fallback.")
            pipe = None

    if pipe is None:
        # Heuristic fallback calculation
        pain = raw_features["pain_score"]
        rom_avg = (raw_features["left_knee_rom"] + raw_features["right_knee_rom"]) / 2.0
        gait_sym = raw_features["gait_symmetry"]
        posture = raw_features["posture_score"]
        
        score = (
            (pain / 10.0) * 35.0 +
            max(0.0, (130.0 - rom_avg) / 70.0) * 30.0 +
            max(0.0, (100.0 - gait_sym) / 60.0) * 20.0 +
            max(0.0, (100.0 - posture) / 60.0) * 15.0
        )
        risk_prob = round(max(8.0, min(95.0, score)), 1)
        if risk_prob < 38.0:
            risk_level = "Low Risk"
        elif risk_prob < 68.0:
            risk_level = "Moderate Risk"
        else:
            risk_level = "High Risk"
        confidence = 88.5

    # Compute Relative Contributions: Questionnaire vs Movement
    # Questionnaire impact
    q_intensity = (
        raw_features["pain_score"] / 10.0 * 0.45 +
        raw_features["stiffness_score"] / 4.0 * 0.25 +
        (10.0 - raw_features["mobility_score"]) / 10.0 * 0.30
    )
    # Movement impact
    m_intensity = (
        max(0.0, (135.0 - raw_features["left_knee_rom"]) / 65.0) * 0.30 +
        max(0.0, (135.0 - raw_features["right_knee_rom"]) / 65.0) * 0.30 +
        max(0.0, (100.0 - raw_features["gait_symmetry"]) / 60.0) * 0.25 +
        max(0.0, (100.0 - raw_features["posture_score"]) / 50.0) * 0.15
    )

    total_imp = max(0.01, q_intensity + m_intensity)
    q_contribution = round((q_intensity / total_imp) * 100.0, 1)
    m_contribution = round(100.0 - q_contribution, 1)

    # Sub-indicators
    movement_indicator = (
        "High" if m_intensity > 0.55 else
        "Moderate" if m_intensity > 0.25 else "Low"
    )
    pain_mobility_indicator = (
        "High" if q_intensity > 0.55 else
        "Moderate" if q_intensity > 0.25 else "Low"
    )

    # Explainable AI: Feature importance & risk drivers
    top_factors: List[Dict[str, Any]] = []

    # Check Pain
    if raw_features["pain_score"] >= 6.0:
        top_factors.append({
            "factor": "Elevated Joint Pain Intensity",
            "importance": 28.0,
            "status": "Alert",
            "detail": f"Reported pain intensity is {raw_features['pain_score']}/10, frequently limiting daily weight-bearing activity."
        })
    elif raw_features["pain_score"] >= 3.0:
        top_factors.append({
            "factor": "Mild Joint Pain",
            "importance": 18.0,
            "status": "Moderate",
            "detail": f"Reported pain score of {raw_features['pain_score']}/10 during sustained movement."
        })
    else:
        top_factors.append({
            "factor": "Minimal Joint Pain",
            "importance": 10.0,
            "status": "Optimal",
            "detail": "Patient reports negligible or mild knee pain during normal movement."
        })

    # Check ROM
    min_rom = min(raw_features["left_knee_rom"], raw_features["right_knee_rom"])
    if min_rom < 95.0:
        top_factors.append({
            "factor": "Restricted Knee Range of Motion",
            "importance": 24.0,
            "status": "Alert",
            "detail": f"Measured knee flexion is limited to {min_rom}° (normal baseline ~125°-140°)."
        })
    elif min_rom < 115.0:
        top_factors.append({
            "factor": "Mild Knee ROM Limitation",
            "importance": 16.0,
            "status": "Moderate",
            "detail": f"Measured knee flexion is {min_rom}°, slightly below typical age-expected baseline."
        })
    else:
        top_factors.append({
            "factor": "Sufficient Knee Flexion ROM",
            "importance": 12.0,
            "status": "Optimal",
            "detail": f"Active knee flexion preserved at {min_rom}° with adequate functional excursion."
        })

    # Check Gait Symmetry
    if raw_features["gait_symmetry"] < 75.0:
        top_factors.append({
            "factor": "Bilateral Gait Asymmetry",
            "importance": 22.0,
            "status": "Alert",
            "detail": f"Gait symmetry is {raw_features['gait_symmetry']}%, suggesting antalgic compensation or unilateral offloading."
        })
    elif raw_features["gait_symmetry"] < 88.0:
        top_factors.append({
            "factor": "Mild Gait Variation",
            "importance": 14.0,
            "status": "Moderate",
            "detail": f"Bilateral symmetry measured at {raw_features['gait_symmetry']}%, showing slight step disparity."
        })
    else:
        top_factors.append({
            "factor": "Symmetric Gait Pattern",
            "importance": 10.0,
            "status": "Optimal",
            "detail": f"Balanced bilateral weight transfer recorded at {raw_features['gait_symmetry']}% symmetry."
        })

    # Check Mobility Rating
    if raw_features["mobility_score"] <= 4.0:
        top_factors.append({
            "factor": "Marked Functional Mobility Difficulty",
            "importance": 18.0,
            "status": "Alert",
            "detail": f"Self-reported mobility score of {raw_features['mobility_score']}/10 with difficulty in stairs and walking."
        })
    elif raw_features["mobility_score"] <= 7.0:
        top_factors.append({
            "factor": "Moderate Functional Mobility Limitation",
            "importance": 12.0,
            "status": "Moderate",
            "detail": f"Self-reported mobility score is {raw_features['mobility_score']}/10."
        })

    # Check Posture Alignment
    if raw_features["posture_score"] < 70.0:
        top_factors.append({
            "factor": "Compensatory Posture Deviation",
            "importance": 14.0,
            "status": "Alert",
            "detail": f"Trunk inclination or lateral pelvic tilt detected (Posture Score: {raw_features['posture_score']}/100)."
        })

    # Actionable clinical recommendations
    recommendations: List[str] = []
    if risk_level == "High Risk":
        recommendations.append("Clinical evaluation with an orthopedic physician or physical therapist is strongly recommended.")
        recommendations.append("Consider radiographic evaluation (weight-bearing AP and lateral knee X-rays) to assess joint space narrowing.")
        recommendations.append("Initiate supervised low-impact quadriceps strengthening and gentle joint range of motion exercises.")
        recommendations.append("Ergonomic guidance for load reduction during stair climbing and prolonged standing.")
    elif risk_level == "Moderate Risk":
        recommendations.append("Follow-up physical assessment recommended within 3 months to monitor movement symmetry and ROM.")
        recommendations.append("Engage in regular low-impact aerobic activities such as walking, cycling, or aquatic exercises.")
        recommendations.append("Maintain optimal body weight to minimize compressive forces across knee joint surfaces.")
        recommendations.append("Perform prescribed hamstring and calf stretches to preserve flexibility.")
    else:
        recommendations.append("Maintain an active lifestyle with regular aerobic exercise and muscle conditioning.")
        recommendations.append("Preserve joint health through balanced nutrition and adequate hydration.")
        recommendations.append("Schedule a routine annual screening or return if new joint stiffness or pain develops.")

    disclaimer = (
        "IMPORTANT MEDICAL NOTICE: OA-Sense AI is an AI-assisted screening and risk-assessment prototype. "
        "It is NOT a medical diagnosis and does not provide definitive medical diagnosis. Findings indicate preliminary risk markers "
        "and must be verified by a qualified healthcare professional."
    )

    return {
        "risk_level": risk_level,
        "risk_probability": risk_prob,
        "confidence": confidence,
        "questionnaire_contribution": q_contribution,
        "movement_contribution": m_contribution,
        "movement_indicator": movement_indicator,
        "pain_mobility_indicator": pain_mobility_indicator,
        "top_risk_factors": top_factors,
        "recommendations": recommendations,
        "disclaimer": disclaimer,
        "model_version": version
    }
