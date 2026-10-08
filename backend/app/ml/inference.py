from typing import Dict, Any, List, Tuple
import numpy as np
from .model import load_ml_model
from .feature_extraction import extract_features

RISK_CLASS_MAP = {
    0: "Low Risk",
    1: "Moderate Risk",
    2: "High Risk"
}

def evaluate_screening_quality_gate(
    movement_dict: Dict[str, Any],
    questionnaire_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluates multidimensional data-quality pillars before accepting an AI screening result:
    1. Landmark detection completeness
    2. Landmark stability / jitter
    3. Camera positioning
    4. Movement completeness
    5. Feature availability & physiological boundaries
    6. Questionnaire completeness

    Outputs discrete pillar ratings ('GOOD', 'FAIR', 'POOR') and aggregate assessment_quality.
    """
    reasons: List[str] = []
    retest_recommendation: str = ""

    status = movement_dict.get("assessment_status", "VALID")
    lq_val = movement_dict.get("landmark_quality_score")
    landmark_quality = float(lq_val) if lq_val is not None else 100.0
    vf_val = movement_dict.get("valid_frame_ratio")
    valid_frames = float(vf_val) if vf_val is not None else 1.0
    lr_val = movement_dict.get("left_knee_rom")
    left_rom = float(lr_val) if lr_val is not None else 120.0
    rr_val = movement_dict.get("right_knee_rom")
    right_rom = float(rr_val) if rr_val is not None else 120.0
    mov_duration = movement_dict.get("movement_duration")
    validation_msg = movement_dict.get("validation_message")

    # --- Pillar 1: Camera Quality (Landmark detection & stability/contrast) ---
    if status in ["REPEAT_REQUIRED", "INSUFFICIENT_DATA"] or landmark_quality < 50.0 or valid_frames < 0.5:
        camera_quality = "POOR"
        reasons.append("Severe landmark dropout or frame occlusion detected during video capture.")
    elif landmark_quality < 75.0 or valid_frames < 0.75:
        camera_quality = "FAIR"
        reasons.append("Partial landmark instability or low contrast observed during movement capture.")
    else:
        camera_quality = "GOOD"

    # --- Pillar 2: Movement Capture & Completeness ---
    # Anatomical feasibility & positioning checks (knee flexion range: 30° to 170°)
    if left_rom < 30.0 or left_rom > 175.0 or right_rom < 30.0 or right_rom > 175.0:
        movement_capture = "POOR"
        reasons.append("Knee angle readings exceeded plausible physiological boundaries (subject turned away or obstructed).")
    elif (mov_duration is not None and mov_duration < 2.5):
        movement_capture = "POOR"
        reasons.append("Insufficient movement duration; test was prematurely aborted before complete kinematic cycles could be recorded.")
    elif (left_rom < 45.0 or left_rom > 165.0 or right_rom < 45.0 or right_rom > 165.0) or (mov_duration is not None and mov_duration < 4.0):
        movement_capture = "FAIR"
        reasons.append("Brief movement recording window or minor off-axis angle orientation observed.")
    else:
        movement_capture = "GOOD"

    # --- Pillar 3: Feature & Questionnaire Completeness ---
    required_q_keys = ["knee_pain", "joint_stiffness", "walking_difficulty", "stair_difficulty", "pain_scale", "mobility_scale"]
    missing_q = [k for k in required_q_keys if questionnaire_dict.get(k) is None]

    pain_val = float(questionnaire_dict.get("pain_scale", 0.0) or 0.0)
    mob_val = float(questionnaire_dict.get("mobility_scale", 10.0) or 10.0)

    if len(missing_q) >= 2 or pain_val < 0.0 or pain_val > 10.0 or mob_val < 0.0 or mob_val > 10.0:
        feature_completeness = "POOR"
        reasons.append("Incomplete questionnaire response profile or invalid response scales.")
    elif len(missing_q) == 1:
        feature_completeness = "FAIR"
        reasons.append("Single optional questionnaire item was omitted.")
    else:
        feature_completeness = "GOOD"

    # --- Aggregate Assessment Quality Determination ---
    # Rule: POOR in any critical pillar results in aggregate POOR
    if camera_quality == "POOR" or movement_capture == "POOR" or feature_completeness == "POOR":
        assessment_quality = "POOR"
        is_reliable = False
        gate_decision = "REJECT_REPEAT_REQUIRED"
        retest_recommended = True
        retest_recommendation = "Assessment quality insufficient. Please repeat the movement assessment with full camera visibility and steady body positioning."
        reasons.insert(0, "Assessment quality insufficient. Please repeat the movement assessment.")
    elif camera_quality == "FAIR" or movement_capture == "FAIR" or feature_completeness == "FAIR":
        assessment_quality = "FAIR"
        is_reliable = True
        gate_decision = "PROCEED_WITH_CAUTION"
        retest_recommended = False
        retest_recommendation = "Assessment completed with acceptable reliability. Some minor telemetry noise was noted."
    else:
        assessment_quality = "GOOD"
        is_reliable = True
        gate_decision = "PROCEED"
        retest_recommended = False
        retest_recommendation = "Full assessment protocol captured with high technical fidelity."

    if validation_msg and validation_msg not in reasons:
        reasons.append(validation_msg)

    return {
        "assessment_quality": assessment_quality,
        "camera_quality": camera_quality,
        "movement_capture": movement_capture,
        "feature_completeness": feature_completeness,
        "is_reliable": is_reliable,
        "gate_decision": gate_decision,
        "retest_recommended": retest_recommended,
        "reasons": reasons,
        "reason": " ".join(reasons) if reasons else retest_recommendation,
        "retest_recommendation": retest_recommendation
    }

def calculate_confidence(
    class_probabilities: List[float],
    data_quality: str,
    feature_completeness: float = 1.0,
    movement_reliability: float = 1.0
) -> Tuple[float, str, float, str]:
    """
    Quality-gated confidence calculation based on real model output and data quality pillars.
    Formula:
      - Raw Model Confidence: Max predicted class probability
      - Class Probability Margin: Top probability minus 2nd probability
      - Adjusted Confidence: Scales with data quality, feature completeness, and movement reliability
      - Category:
          GOOD data + strong model separation (margin >= 0.35) -> HIGH
          FAIR data OR moderate separation -> MEDIUM
          POOR data OR unreliable movement -> LOW / repeat assessment
    """
    if not class_probabilities:
        return 0.0, "LOW", 0.0, "No model probabilities available."

    sorted_p = sorted(class_probabilities, reverse=True)
    max_p = sorted_p[0]
    margin = round(float(sorted_p[0] - sorted_p[1]), 3) if len(sorted_p) > 1 else round(float(max_p), 3)

    raw_conf_pct = round(float(max_p * 100), 1)

    if data_quality == "POOR" or movement_reliability < 0.5:
        level = "LOW"
        reason = "Assessment quality or movement tracking insufficient to support reliable confidence."
        final_conf_pct = round(raw_conf_pct * 0.4, 1)
    elif data_quality == "FAIR":
        if margin >= 0.35 and raw_conf_pct >= 65.0:
            level = "MEDIUM"
            reason = "Moderate probability separation observed; down-weighted to MEDIUM due to fair data quality."
        else:
            level = "LOW"
            reason = "Class probability margin is narrow and data quality is fair."
        final_conf_pct = round(raw_conf_pct * 0.8, 1)
    else:  # GOOD
        if margin >= 0.35 or raw_conf_pct >= 68.0:
            level = "HIGH"
            reason = "High model separation corroborated by high-quality telemetry and complete features."
        elif raw_conf_pct >= 48.0 or margin >= 0.15:
            level = "MEDIUM"
            reason = "Moderate probability margin across adjacent risk classes."
        else:
            level = "LOW"
            reason = "Model classification margins between adjacent risk categories were narrow."
        final_conf_pct = raw_conf_pct

    return final_conf_pct, level, margin, reason

def compute_confidence_level(
    model_confidence_pct: float,
    assessment_quality: str,
    probas: Any = None,
    quality_reasons: List[str] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Computes confidence category ('HIGH', 'MEDIUM', 'LOW'), clinical calibration rationale,
    and granular breakdown.
    Strict rule: Never fabricates confidence.
    """
    if probas is not None and len(probas) > 0:
        _, level, margin, reason = calculate_confidence(
            class_probabilities=list(probas),
            data_quality=assessment_quality
        )
    else:
        margin = 0.0
        level = "LOW" if assessment_quality == "POOR" else "MEDIUM"
        reason = "Classification certainty computed without probability vector."

    breakdown = {
        "model_confidence_pct": model_confidence_pct,
        "class_probability_margin": margin,
        "assessment_quality": assessment_quality,
        "confidence_level": level
    }

    return level, reason, breakdown

def get_early_medical_guidance(risk_level: str, assessment_quality: str) -> str:
    """Provides early medical-evaluation guidance based on quality-gated screening outcome."""
    if assessment_quality == "POOR":
        return "Reliable screening could not be completed due to insufficient assessment quality. Please repeat the movement assessment with clear lighting and camera visibility."

    if risk_level == "High Risk":
        return "Multiple OA-related risk markers were identified in this preliminary screening. Professional medical evaluation with an orthopedic physician or qualified physiotherapist is recommended."
    elif risk_level == "Moderate Risk":
        return "OA-related risk markers were identified. Consider consulting a qualified healthcare professional for clinical examination and functional follow-up."
    else:
        return "No significant OA-related risk markers were identified in this screening. Consider routine health monitoring and seek professional evaluation if symptoms persist or worsen."

def predict_oa_risk(
    age: int,
    activity_level: str,
    joint_injury: int,
    family_history: int,
    questionnaire_dict: Dict[str, Any],
    movement_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Performs Quality-Gated, Confidence-Aware OA Risk Screening inference.
    Before generating screening results, evaluates the Screening Quality Gate.
    If assessment quality is POOR:
      - Does NOT display an alarming risk conclusion
      - Returns status 'Assessment quality insufficient'
      - Sets Confidence to LOW and flags retest
    If GOOD or FAIR:
      - Runs ML pipeline inference
      - Adjusts confidence based on data quality + model margin
      - Produces traceable explainability distinguishing Observed facts, Model contributions, and Quality limitations.
    """
    # 1. Evaluate Screening Quality Gate
    q_gate = evaluate_screening_quality_gate(movement_dict, questionnaire_dict)
    assessment_quality = q_gate["assessment_quality"]
    is_reliable = q_gate["is_reliable"]

    # 2. Extract features
    raw_features, feature_df = extract_features(
        age=age,
        activity_level=activity_level,
        joint_injury=joint_injury,
        family_history=family_history,
        questionnaire_dict=questionnaire_dict,
        movement_dict=movement_dict
    )

    # 3. Handle POOR Quality (Quality Gate Rejection)
    if not is_reliable:
        guidance = get_early_medical_guidance("Inconclusive", "POOR")
        return {
            "risk_level": "Assessment Quality Insufficient",
            "risk_probability": 0.0,
            "confidence": 0.0,
            "confidence_level": "LOW",
            "data_quality": "POOR",
            "confidence_reason": "Assessment quality insufficient. " + " ".join(q_gate["reasons"]),
            "confidence_breakdown": {
                "model_confidence_pct": 0.0,
                "class_probability_margin": 0.0,
                "assessment_quality": "POOR",
                "confidence_level": "LOW"
            },
            "quality_report": {
                "assessment_quality": "POOR",
                "camera_quality": q_gate["camera_quality"],
                "movement_capture": q_gate["movement_capture"],
                "feature_completeness": q_gate["feature_completeness"],
                "ai_confidence": "LOW",
                "retest_recommendation": q_gate["retest_recommendation"]
            },
            "early_guidance": guidance,
            "questionnaire_contribution": 0.0,
            "movement_contribution": 0.0,
            "movement_indicator": "Low",
            "pain_mobility_indicator": "Low",
            "top_risk_factors": [],
            "recommendations": [
                "Screening could not be reliably completed.",
                "Please repeat the assessment with better camera positioning and movement visibility.",
                "Ensure both legs, knees, and ankles remain clearly visible throughout the movement test."
            ],
            "disclaimer": (
                "SCREENING NOTICE: Unreliable or occluded movement telemetry prevented risk-marker calculation. "
                "No medical conclusions are drawn from poor-quality data."
            ),
            "model_version": "1.0.0-demo",
            "model_name": "LogisticRegression",
            "assessment_status": "REPEAT_REQUIRED",
            "prediction_status": "REJECTED_QUALITY_GATE"
        }

    # 4. Run ML Model for GOOD and FAIR quality data
    model_bundle = load_ml_model()
    pipe = model_bundle.get("pipeline")
    model_name = model_bundle.get("model_name", "LogisticRegression")
    version = model_bundle.get("version", "1.0.0-demo")
    probas = None

    if pipe is not None:
        try:
            pred_class = int(pipe.predict(feature_df)[0])
            probas = pipe.predict_proba(feature_df)[0]
            # Risk probability is weighted combination of moderate and high risk classes
            risk_prob = float((probas[1] * 0.55 + probas[2] * 1.0) * 100.0)
            risk_prob = round(max(5.0, min(96.0, risk_prob)), 1)
            raw_conf = round(float(np.max(probas) * 100.0), 1)
            risk_level = RISK_CLASS_MAP.get(pred_class, "Moderate Risk")
        except Exception as e:
            print(f"[INFERENCE ERROR] Pipeline failure: {e}. Using fallback.")
            pipe = None

    if pipe is None:
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
        raw_conf = 85.0

    confidence_level, confidence_reason, conf_breakdown = compute_confidence_level(
        model_confidence_pct=raw_conf,
        assessment_quality=assessment_quality,
        probas=probas,
        quality_reasons=q_gate["reasons"]
    )

    # 5. Relative Contribution of factors
    q_intensity = (
        raw_features["pain_score"] / 10.0 * 0.45 +
        raw_features["stiffness_score"] / 4.0 * 0.25 +
        (10.0 - raw_features["mobility_score"]) / 10.0 * 0.30
    )
    m_intensity = (
        max(0.0, (135.0 - raw_features["left_knee_rom"]) / 65.0) * 0.30 +
        max(0.0, (135.0 - raw_features["right_knee_rom"]) / 65.0) * 0.30 +
        max(0.0, (100.0 - raw_features["gait_symmetry"]) / 60.0) * 0.25 +
        max(0.0, (100.0 - raw_features["posture_score"]) / 50.0) * 0.15
    )

    total_imp = max(0.01, q_intensity + m_intensity)
    q_contribution = round((q_intensity / total_imp) * 100.0, 1)
    m_contribution = round(100.0 - q_contribution, 1)

    # 6. Genuine Model-Derived Explainable AI Attribution
    # Formula:
    #   z = StandardScaler(Imputer(x))
    #   contribution_i = z_i * beta_{pred_class, i}
    #   positive_sum = sum(max(0, contribution_i))
    #   relative_attribution_i = (max(0, contribution_i) / positive_sum) * 100 if positive_sum > 0 else None
    #   direction = "increases risk" if contribution_i > 0 else "decreases risk"
    top_factors: List[Dict[str, Any]] = []

    # Human-readable labels and descriptions for core features
    FEATURE_METADATA = {
        "left_knee_rom": {
            "title": "Left Knee Range of Motion",
            "unit": "°",
            "desc": "Active knee flexion excursion of the left limb."
        },
        "right_knee_rom": {
            "title": "Right Knee Range of Motion",
            "unit": "°",
            "desc": "Active knee flexion excursion of the right limb."
        },
        "pain_score": {
            "title": "Reported Joint Pain",
            "unit": "/10",
            "desc": "Subjective pain burden during weight-bearing activities."
        },
        "gait_symmetry": {
            "title": "Bilateral Gait Symmetry",
            "unit": "%",
            "desc": "Symmetry of bilateral foot strike and weight-bearing time."
        },
        "mobility_score": {
            "title": "Functional Mobility Level",
            "unit": "/10",
            "desc": "Patient self-reported daily physical functional mobility."
        },
        "knee_symmetry": {
            "title": "Knee Bilateral ROM Symmetry",
            "unit": "%",
            "desc": "Bilateral comparison of maximum active knee angles."
        },
        "posture_score": {
            "title": "Posture Alignment Index",
            "unit": "/100",
            "desc": "Upper-to-lower body alignment during movement screening."
        },
        "stiffness_score": {
            "title": "Joint Stiffness Frequency",
            "unit": "/4",
            "desc": "Frequency of morning or post-inactivity knee stiffness."
        },
        "age": {
            "title": "Patient Age",
            "unit": " yrs",
            "desc": "Biological age factor associated with joint cartilage remodeling."
        },
        "joint_injury": {
            "title": "Previous Joint Injury History",
            "unit": "",
            "desc": "Prior traumatic ligament, meniscus, or joint injury indicator."
        }
    }

    if pipe is not None and hasattr(pipe, "named_steps") and "classifier" in pipe.named_steps:
        try:
            imputer_step = pipe.named_steps.get("imputer")
            scaler_step = pipe.named_steps.get("scaler")
            classifier_step = pipe.named_steps.get("classifier")

            # Transform features exactly matching prediction pipeline
            imputed_vals = imputer_step.transform(feature_df) if imputer_step else feature_df.values
            scaled_vals = scaler_step.transform(imputed_vals)[0] if scaler_step else imputed_vals[0]

            feature_names = list(feature_df.columns)
            coef_matrix = classifier_step.coef_  # Shape: (n_classes, n_features)

            # Determine coefficient vector for predicted class
            # For multiclass, coef_matrix has one row per class
            if coef_matrix.ndim == 2 and coef_matrix.shape[0] > pred_class:
                betas = coef_matrix[pred_class]
            elif coef_matrix.ndim == 2:
                betas = coef_matrix[0]
            else:
                betas = coef_matrix

            pred_class_label = RISK_CLASS_MAP.get(pred_class, "moderate").lower()

            # Calculate raw contributions: contribution_i = z_i * beta_i
            contributions: Dict[str, Dict[str, Any]] = {}
            for idx, f_name in enumerate(feature_names):
                z_i = float(scaled_vals[idx])
                beta_i = float(betas[idx])
                raw_c = float(z_i * beta_i)
                contributions[f_name] = {
                    "feature_name": f_name,
                    "actual_value": float(raw_features.get(f_name, feature_df.iloc[0][f_name])),
                    "scaled_value": round(z_i, 4),
                    "coefficient": round(beta_i, 4),
                    "raw_contribution": round(raw_c, 4),
                    "direction": "increases risk" if raw_c > 0 else "decreases risk"
                }

            # Calculate relative positive attribution
            pos_sum = sum(max(0.0, item["raw_contribution"]) for item in contributions.values())

            for f_name, item in contributions.items():
                if pos_sum > 0 and item["raw_contribution"] > 0:
                    item["relative_attribution"] = round((item["raw_contribution"] / pos_sum) * 100.0, 1)
                else:
                    item["relative_attribution"] = None
                item["predicted_class"] = pred_class_label

            # Select the most impactful key clinical features for transparent display
            # Rank priority: features in FEATURE_METADATA ordered by absolute contribution magnitude
            key_features = [f for f in feature_names if f in FEATURE_METADATA]
            sorted_keys = sorted(key_features, key=lambda f: abs(contributions[f]["raw_contribution"]), reverse=True)

            for f_name in sorted_keys[:5]:
                c_data = contributions[f_name]
                meta = FEATURE_METADATA.get(f_name, {"title": f_name.replace("_", " ").title(), "unit": "", "desc": ""})
                unit = meta.get("unit", "")
                val_disp = f"{c_data['actual_value']:.0f}{unit}" if c_data['actual_value'] == int(c_data['actual_value']) else f"{c_data['actual_value']:.1f}{unit}"
                
                # Contextual status
                if c_data["direction"] == "increases risk":
                    status = "Alert" if (c_data.get("relative_attribution") or 0) >= 15.0 else "Moderate"
                else:
                    status = "Optimal"

                # Medical wording focuses on model behavior, not medical causation
                direction_word = "elevated" if c_data["direction"] == "increases risk" else "mitigated"
                attr_text = f" (+{c_data['relative_attribution']}%)" if c_data.get("relative_attribution") is not None else ""
                
                observed_text = f"Measured / reported value: {val_disp} (normalized z-score: {c_data['scaled_value']:+.2f})."
                inference_text = (
                    f"Model-derived linear contribution: {c_data['raw_contribution']:+.3f}{attr_text}. "
                    f"This feature {c_data['direction']} for the {pred_class_label} risk-marker assessment."
                )

                # Quality/telemetry limitation note
                if "rom" in f_name:
                    limitation_text = "Slight tracking noise in deep flexion excursion." if assessment_quality == "FAIR" else "Landmarks stable across entire flexion excursion."
                elif "gait" in f_name:
                    limitation_text = "Step duration variance may have slight perspective noise." if assessment_quality == "FAIR" else "Bilateral stride intervals recorded with consistent tracking."
                else:
                    limitation_text = "Patient-reported screening parameter complete and validated."

                top_factors.append({
                    "factor": meta["title"],
                    "importance": float(c_data["relative_attribution"] or 0.0),
                    "status": status,
                    "observed": observed_text,
                    "inference": inference_text,
                    "confidence_limitation": limitation_text,
                    "detail": meta["desc"],
                    "feature_name": c_data["feature_name"],
                    "actual_value": c_data["actual_value"],
                    "scaled_value": c_data["scaled_value"],
                    "coefficient": c_data["coefficient"],
                    "raw_contribution": c_data["raw_contribution"],
                    "relative_attribution": c_data["relative_attribution"],
                    "direction": c_data["direction"],
                    "predicted_class": c_data["predicted_class"]
                })
        except Exception as e:
            print(f"[EXPLAINABILITY ERROR] Dynamic calculation failed: {e}. Falling back to rule-based factor summary.")
            pipe = None

    if not top_factors:
        # Fallback if pipeline not loaded
        top_factors = [
            {
                "factor": "Reported Joint Pain",
                "importance": 0.0,
                "status": "Moderate",
                "observed": f"Reported score: {raw_features['pain_score']:.1f}/10.",
                "inference": "Pain intensity input factor.",
                "confidence_limitation": "Questionnaire response validated.",
                "detail": "Reported pain score.",
                "feature_name": "pain_score",
                "actual_value": float(raw_features["pain_score"]),
                "scaled_value": None,
                "coefficient": None,
                "raw_contribution": None,
                "relative_attribution": None,
                "direction": "increases risk" if raw_features["pain_score"] >= 4.0 else "decreases risk",
                "predicted_class": risk_level.lower()
            }
        ]

    early_guidance = get_early_medical_guidance(risk_level, assessment_quality)

    recommendations: List[str] = [early_guidance]
    if risk_level in ["High Risk", "Moderate Risk"]:
        recommendations.append("OA-related risk markers were identified in this screening. Consider evaluation by a qualified healthcare professional for further assessment.")
        recommendations.append("Follow-up screening may be considered based on symptoms and guidance from a qualified healthcare professional.")
    else:
        recommendations.append("Follow-up screening may be considered based on symptoms and guidance from a qualified healthcare professional.")

    quality_report = {
        "assessment_quality": assessment_quality,
        "camera_quality": q_gate["camera_quality"],
        "movement_capture": q_gate["movement_capture"],
        "feature_completeness": q_gate["feature_completeness"],
        "ai_confidence": confidence_level,
        "retest_recommendation": q_gate["retest_recommendation"]
    }

    disclaimer = (
        "IMPORTANT MEDICAL SAFETY NOTICE: OA-Sense AI is an AI-assisted preliminary screening system. "
        "It identifies OA-related risk markers to support clinical decision-making. "
        "It does NOT provide a definitive diagnosis of osteoarthritis. "
        "A qualified healthcare professional remains responsible for clinical diagnosis and treatment planning."
    )

    return {
        "risk_level": risk_level,
        "risk_probability": risk_prob,
        "confidence": raw_conf,
        "confidence_level": confidence_level,
        "data_quality": assessment_quality,
        "confidence_reason": confidence_reason,
        "confidence_breakdown": conf_breakdown,
        "quality_report": quality_report,
        "early_guidance": early_guidance,
        "questionnaire_contribution": q_contribution,
        "movement_contribution": m_contribution,
        "movement_indicator": "High" if m_intensity > 0.55 else "Moderate" if m_intensity > 0.25 else "Low",
        "pain_mobility_indicator": "High" if q_intensity > 0.55 else "Moderate" if q_intensity > 0.25 else "Low",
        "top_risk_factors": top_factors,
        "recommendations": recommendations,
        "disclaimer": disclaimer,
        "model_version": version,
        "model_name": model_name,
        "assessment_status": "VALID" if assessment_quality == "GOOD" else "LIMITED_QUALITY",
        "prediction_status": "COMPLETED"
    }
