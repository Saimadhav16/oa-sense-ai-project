import os
import datetime
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable

def generate_pdf_report(
    patient_data: dict,
    screening_data: dict,
    prediction_data: dict,
    output_dir: str = None
) -> str:
    """
    Generates a professional medical screening report in PDF format using ReportLab.
    Includes patient demographics, ML risk assessment, biomechanical metrics,
    explainability breakdown, clinical recommendations, and required medical disclaimers.
    """
    if output_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        output_dir = os.path.join(base_dir, "reports")
    os.makedirs(output_dir, exist_ok=True)

    screening_id = screening_data.get("id", "SCR")
    timestamp_str = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_name = f"OA_Screening_{patient_data.get('patient_code', 'P')}_{screening_id}_{timestamp_str}.pdf"
    file_path = os.path.join(output_dir, file_name)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#0D9488")    # Teal 600
    c_secondary = colors.HexColor("#0F766E")  # Teal 700
    c_dark = colors.HexColor("#1E293B")       # Slate 800
    c_muted = colors.HexColor("#64748B")      # Slate 500
    c_card_bg = colors.HexColor("#F8FAFC")    # Slate 50
    c_border = colors.HexColor("#E2E8F0")     # Slate 200

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=c_secondary,
        leading=24
    )
    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=c_muted,
        leading=14
    )
    section_heading = ParagraphStyle(
        "SectionHead",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=c_dark,
        leading=16,
        spaceBefore=8,
        spaceAfter=4
    )
    normal_text = ParagraphStyle(
        "NormalText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=c_dark,
        leading=13
    )
    bold_label = ParagraphStyle(
        "BoldLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=c_dark,
        leading=13
    )
    disclaimer_text = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=colors.HexColor("#991B1B"),
        leading=11
    )

    elements = []

    # 1. Header Banner
    elements.append(Paragraph("OA-Sense AI", title_style))
    elements.append(Paragraph("AI-Assisted Early Osteoarthritis Risk Screening System | Community Health Screening Report", subtitle_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceAfter=12))

    # 2. Patient Demographics & Screening Metadata Table
    scr_date = screening_data.get("screening_date", datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
    if isinstance(scr_date, datetime.datetime):
        scr_date = scr_date.strftime("%Y-%m-%d %H:%M UTC")

    patient_table_data = [
        [
            Paragraph("<b>Patient Name:</b>", normal_text),
            Paragraph(str(patient_data.get("name", "N/A")), normal_text),
            Paragraph("<b>Patient Code / ID:</b>", normal_text),
            Paragraph(str(patient_data.get("patient_code", "N/A")), normal_text),
        ],
        [
            Paragraph("<b>Age / Gender:</b>", normal_text),
            Paragraph(f"{patient_data.get('age', 'N/A')} yrs / {patient_data.get('gender', 'N/A')}", normal_text),
            Paragraph("<b>Screening Date:</b>", normal_text),
            Paragraph(str(scr_date), normal_text),
        ],
        [
            Paragraph("<b>Occupation:</b>", normal_text),
            Paragraph(str(patient_data.get("occupation", "N/A")), normal_text),
            Paragraph("<b>Activity Level:</b>", normal_text),
            Paragraph(str(patient_data.get("activity_level", "Moderate")), normal_text),
        ]
    ]

    patient_table = Table(patient_table_data, colWidths=[105, 160, 115, 160])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_card_bg),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(patient_table)
    elements.append(Spacer(1, 14))

    # 3. Overall Screening Risk Assessment Banner
    risk_level = prediction_data.get("risk_level", screening_data.get("risk_level", "Moderate Risk"))
    risk_prob = prediction_data.get("risk_probability", screening_data.get("risk_probability", 50.0))
    conf = prediction_data.get("confidence", screening_data.get("confidence", 90.0))

    if "high" in risk_level.lower():
        risk_bg = colors.HexColor("#FEE2E2")
        risk_color = colors.HexColor("#B91C1C")
    elif "moderate" in risk_level.lower():
        risk_bg = colors.HexColor("#FEF3C7")
        risk_color = colors.HexColor("#B45309")
    else:
        risk_bg = colors.HexColor("#DCFCE7")
        risk_color = colors.HexColor("#15803D")

    risk_style = ParagraphStyle(
        "RiskStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=risk_color,
        leading=18
    )

    conf_lvl = prediction_data.get("confidence_level", screening_data.get("confidence_level", "HIGH"))
    data_qual = prediction_data.get("data_quality", screening_data.get("data_quality", "GOOD"))
    conf_reason = prediction_data.get("confidence_reason", screening_data.get("confidence_reason", ""))

    q_cont = prediction_data.get("questionnaire_contribution", screening_data.get("questionnaire_contribution", 50.0))
    m_cont = prediction_data.get("movement_contribution", screening_data.get("movement_contribution", 50.0))

    # Screening Quality Report Section
    q_report = prediction_data.get("quality_report") or screening_data.get("quality_report")
    if isinstance(q_report, str):
        try:
            import json
            q_report = json.loads(q_report)
        except Exception:
            q_report = None

    if q_report:
        aq = q_report.get("assessment_quality", data_qual)
        cq = q_report.get("camera_quality", "GOOD")
        mc = q_report.get("movement_capture", "GOOD")
        fc = q_report.get("feature_completeness", "GOOD")
        q_reason = q_report.get("reason", "")

        qr_data = [
            [
                Paragraph("<b>SCREENING QUALITY GATE</b>", bold_label),
                Paragraph(f"<b>Assessment:</b> {aq}", bold_label),
                Paragraph(f"<b>Camera:</b> {cq}", bold_label),
                Paragraph(f"<b>Movement:</b> {mc}", bold_label),
                Paragraph(f"<b>Features:</b> {fc}", bold_label),
            ]
        ]
        qr_table = Table(qr_data, colWidths=[140, 100, 100, 100, 100])
        qr_bg = colors.HexColor("#DCFCE7") if aq == "GOOD" else (colors.HexColor("#FEF3C7") if aq == "FAIR" else colors.HexColor("#FEE2E2"))
        qr_border = colors.HexColor("#15803D") if aq == "GOOD" else (colors.HexColor("#B45309") if aq == "FAIR" else colors.HexColor("#B91C1C"))
        qr_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), qr_bg),
            ('BOX', (0, 0), (-1, -1), 1, qr_border),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, qr_border),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(qr_table)
        elements.append(Spacer(1, 6))

    is_poor = (data_qual == "POOR") or (q_report and q_report.get("assessment_quality") == "POOR")

    if is_poor:
        risk_box_data = [
            [
                Paragraph(f"<b>SCREENING STATUS:</b> <br/><font size=14 color='#B91C1C'>INCONCLUSIVE</font><br/><font size=9 color='#B91C1C'>Assessment Quality Insufficient</font>", risk_style),
                Paragraph(
                    f"<b>Quality Gate Notice:</b> Assessment quality insufficient.<br/>"
                    f"<b>Finding:</b> Screening could not be reliably completed.<br/>"
                    f"<b>AI Confidence:</b> LOW ({conf}%) | <b>Data Quality:</b> POOR<br/>"
                    f"<b>Guidance:</b> Please repeat the movement assessment with better camera positioning and movement visibility.",
                    normal_text
                )
            ]
        ]
    else:
        risk_box_data = [
            [
                Paragraph(f"<b>SCREENING RESULT:</b> <br/><font size=16>{risk_level.upper()}</font><br/><font size=9 color='{risk_color}'>AI-Assisted Preliminary Screening</font>", risk_style),
                Paragraph(
                    f"<b>Risk Level:</b> {risk_level}<br/>"
                    f"<b>Confidence:</b> {conf_lvl} ({conf}%) | <b>Data Quality:</b> {data_qual}<br/>"
                    f"<b>Model Calibration:</b> {conf_reason or 'Model classification certainty aligned with input data.'}<br/>"
                    f"<b>Questionnaire Weight:</b> {q_cont}% | <b>Movement Weight:</b> {m_cont}%",
                    normal_text
                )
            ]
        ]

    risk_box_table = Table(risk_box_data, colWidths=[240, 300])
    risk_box_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEE2E2") if is_poor else risk_bg),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#B91C1C") if is_poor else risk_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(risk_box_table)
    elements.append(Spacer(1, 10))

    # Early Guidance Banner if present
    early_guidance = prediction_data.get("early_guidance") or screening_data.get("early_guidance")
    if early_guidance:
        guide_box = [
            [
                Paragraph(f"<b>EARLY MEDICAL-EVALUATION GUIDANCE:</b> {early_guidance}", normal_text)
            ]
        ]
        guide_table = Table(guide_box, colWidths=[540])
        guide_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0FDFA")),
            ('BOX', (0, 0), (-1, -1), 1, c_primary),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(guide_table)
        elements.append(Spacer(1, 10))

    # 4. Biomechanical & Movement Results
    elements.append(Paragraph("1. Computer-Vision Movement Protocol Analysis", section_heading))
    
    # Check if distinct movement_tests dictionary exists
    m_tests = screening_data.get("movement_tests")
    if isinstance(m_tests, str):
        try:
            m_tests = json.loads(m_tests)
        except Exception:
            m_tests = None

    if m_tests and isinstance(m_tests, dict):
        kf = m_tests.get("knee_flexion", {})
        sts = m_tests.get("sit_to_stand", {})
        wk = m_tests.get("walking", {})

        protocol_table_data = [
            [
                Paragraph("<b>Movement Test Protocol</b>", bold_label),
                Paragraph("<b>Biomechanical Findings</b>", bold_label),
                Paragraph("<b>Data Quality</b>", bold_label),
                Paragraph("<b>Status</b>", bold_label)
            ],
            [
                Paragraph("<b>Test 1: Knee Flexion</b><br/><font size=8 color='#64748B'>Knee ROM & Symmetry</font>", normal_text),
                Paragraph(f"L ROM: {kf.get('left_knee_rom', screening_data.get('left_knee_rom', 120.0))}° | R ROM: {kf.get('right_knee_rom', screening_data.get('right_knee_rom', 120.0))}°<br/>Symmetry: {kf.get('knee_symmetry', 95.0)}% | Mean Angle: {kf.get('average_knee_angle', 115.0)}°", normal_text),
                Paragraph(f"Quality: {round(float(kf.get('movement_quality_score', 85.0)), 1)}%<br/>Frames: {kf.get('valid_frames_count', 30)}/{kf.get('total_frames_count', 30)}", normal_text),
                Paragraph(f"<font color='#0D9488'><b>{kf.get('assessment_status', 'VALID')}</b></font>", normal_text)
            ],
            [
                Paragraph("<b>Test 2: Sit-to-Stand</b><br/><font size=8 color='#64748B'>Functional Dynamics</font>", normal_text),
                Paragraph(f"Repetitions: {sts.get('repetition_count', 3)} cycles<br/>Duration: {sts.get('movement_duration', 8.0)}s | Posture: {sts.get('posture_score', 85.0)}/100", normal_text),
                Paragraph(f"Quality: {round(float(sts.get('movement_quality_score', 88.0)), 1)}%<br/>Smoothness: {sts.get('movement_smoothness', 85.0)}%", normal_text),
                Paragraph(f"<font color='#0D9488'><b>{sts.get('assessment_status', 'VALID')}</b></font>", normal_text)
            ],
            [
                Paragraph("<b>Test 3: Walking / Gait</b><br/><font size=8 color='#64748B'>Gait Symmetry & Cadence</font>", normal_text),
                Paragraph(f"Gait Symmetry: {wk.get('gait_symmetry', screening_data.get('gait_symmetry', 90.0))}%<br/>Consistency: {wk.get('movement_consistency', 88.0)}% | Duration: {wk.get('movement_duration', 8.0)}s", normal_text),
                Paragraph(f"Quality: {round(float(wk.get('movement_quality_score', 90.0)), 1)}%<br/>Landmark Quality: {round(float(wk.get('landmark_quality_score', 90.0)), 1)}%", normal_text),
                Paragraph(f"<font color='#0D9488'><b>{wk.get('assessment_status', 'VALID')}</b></font>", normal_text)
            ],
            [
                Paragraph("<b>Overall Assessment Quality</b>", bold_label),
                Paragraph(f"Aggregate Quality: {round(float(screening_data.get('movement_quality_score', 88.0)), 1)}%<br/>Valid Frame Ratio: {round(float(screening_data.get('valid_frame_ratio', 1.0)) * 100, 1)}%", normal_text),
                Paragraph(f"Landmarks: {round(float(screening_data.get('landmark_quality_score', 100.0)), 1)}%", normal_text),
                Paragraph(f"<b>{screening_data.get('assessment_status', 'VALID')}</b>", bold_label)
            ]
        ]
        cv_table = Table(protocol_table_data, colWidths=[150, 180, 120, 90])
    else:
        left_rom = screening_data.get("left_knee_rom", 120.0)
        right_rom = screening_data.get("right_knee_rom", 120.0)
        knee_sym = screening_data.get("knee_symmetry", 95.0)
        gait_sym = screening_data.get("gait_symmetry", 90.0)
        posture_val = screening_data.get("posture_score", 85.0)
        smoothness = screening_data.get("movement_smoothness", 90.0)

        cv_table_data = [
            [
                Paragraph("<b>Metric</b>", bold_label),
                Paragraph("<b>Value</b>", bold_label),
                Paragraph("<b>Prototype Reference</b>", bold_label),
                Paragraph("<b>Observation</b>", bold_label)
            ],
            [
                Paragraph("Left Knee Range of Motion", normal_text),
                Paragraph(f"{left_rom}°", normal_text),
                Paragraph("125° - 145°", normal_text),
                Paragraph("Within reference range" if left_rom >= 125 else ("Borderline" if left_rom >= 115 else "Below reference range"), normal_text)
            ],
            [
                Paragraph("Right Knee Range of Motion", normal_text),
                Paragraph(f"{right_rom}°", normal_text),
                Paragraph("125° - 145°", normal_text),
                Paragraph("Within reference range" if right_rom >= 125 else ("Borderline" if right_rom >= 115 else "Below reference range"), normal_text)
            ],
            [
                Paragraph("Knee ROM Bilateral Symmetry", normal_text),
                Paragraph(f"{knee_sym}%", normal_text),
                Paragraph("&ge; 90%", normal_text),
                Paragraph("Within reference range" if knee_sym >= 90 else ("Borderline" if knee_sym >= 85 else "Below reference range"), normal_text)
            ],
            [
                Paragraph("Gait Symmetry Index", normal_text),
                Paragraph(f"{gait_sym}%", normal_text),
                Paragraph("&ge; 88%", normal_text),
                Paragraph("Within reference range" if gait_sym >= 88 else ("Borderline" if gait_sym >= 83 else "Below reference range"), normal_text)
            ],
            [
                Paragraph("Posture Alignment Score", normal_text),
                Paragraph(f"{posture_val}/100", normal_text),
                Paragraph("&ge; 85/100", normal_text),
                Paragraph("Within reference range" if posture_val >= 85 else ("Borderline" if posture_val >= 80 else "Below reference range"), normal_text)
            ],
            [
                Paragraph("Movement Smoothness", normal_text),
                Paragraph(f"{smoothness}%", normal_text),
                Paragraph("&ge; 85%", normal_text),
                Paragraph("Within reference range" if smoothness >= 85 else ("Borderline" if smoothness >= 80 else "Below reference range"), normal_text)
            ],
            [
                Paragraph("Angular Velocity (Peak L / R)", normal_text),
                Paragraph(f"{screening_data.get('peak_left_velocity') or 45.0}°/s / {screening_data.get('peak_right_velocity') or 45.0}°/s", normal_text),
                Paragraph("Symmetric", normal_text),
                Paragraph(f"Duration: {screening_data.get('movement_duration') or 8.0}s ({screening_data.get('repetition_count') or 0} cycles)", normal_text)
            ],
            [
                Paragraph("Movement Data Quality Score", normal_text),
                Paragraph(f"{round(float(screening_data.get('movement_quality_score', 88.0)), 1)}%", normal_text),
                Paragraph("Technical Reliability", normal_text),
                Paragraph(f"Landmark: {round(float(screening_data.get('landmark_quality_score', 100.0)), 1)}% | Valid: {round(float(screening_data.get('valid_frame_ratio', 1.0)) * 100, 1)}%", normal_text)
            ],
        ]
        cv_table = Table(cv_table_data, colWidths=[160, 90, 130, 160])

    cv_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E0F2FE")),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(cv_table)
    elements.append(Spacer(1, 12))

    # 5. Questionnaire Summary
    elements.append(Paragraph("2. Pain & Mobility Assessment", section_heading))
    pain_val = screening_data.get("pain_score", 0.0)
    stiff_val = screening_data.get("stiffness_score", 0.0)
    mob_val = screening_data.get("mobility_score", 10.0)

    q_summary_data = [
        [
            Paragraph("<b>Reported Pain (0-10 Scale):</b>", normal_text),
            Paragraph(f"{pain_val} / 10", normal_text),
            Paragraph("<b>Joint Stiffness Frequency:</b>", normal_text),
            Paragraph(f"Level {stiff_val} / 4", normal_text)
        ],
        [
            Paragraph("<b>Mobility Rating (0-10 Scale):</b>", normal_text),
            Paragraph(f"{mob_val} / 10", normal_text),
            Paragraph("<b>Pain During Stairs / Walk:</b>", normal_text),
            Paragraph("Present" if pain_val >= 3.0 else "Minimal / None", normal_text)
        ]
    ]
    q_table = Table(q_summary_data, colWidths=[160, 110, 160, 110])
    q_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_card_bg),
        ('BOX', (0, 0), (-1, -1), 1, c_border),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(q_table)
    elements.append(Spacer(1, 12))

    # 6. Top Risk Indicators & Traceable Explainability
    elements.append(Paragraph("3. Explainable Risk Factors (Observed vs Model Inference)", section_heading))
    top_factors = prediction_data.get("top_risk_factors") or screening_data.get("top_risk_factors")
    if not top_factors and screening_data.get("explainability_json"):
        try:
            exp_raw = screening_data.get("explainability_json")
            top_factors = json.loads(exp_raw) if isinstance(exp_raw, str) else exp_raw
        except Exception:
            top_factors = []

    if not top_factors:
        elements.append(Paragraph("• No severe abnormal movement or pain markers detected in this screening session.", normal_text))
    else:
        for tf in top_factors[:5]:
            f_name = tf.get("factor") or tf.get("feature_name", "Factor")
            f_stat = tf.get("status", "Info")
            f_obs = tf.get("observed")
            f_inf = tf.get("inference")
            f_det = tf.get("detail", "")
            f_dir = tf.get("direction")
            f_attr = tf.get("relative_attribution")
            
            dir_label = f" | {f_dir.upper()}" if f_dir else ""
            elements.append(Paragraph(f"• <b>{f_name}</b> [{f_stat}{dir_label}]", bold_label))
            if f_obs:
                elements.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Observed:</b> {f_obs}", normal_text))
            if f_inf:
                elements.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;<b>Model Contribution:</b> {f_inf}", normal_text))
            if not f_obs and not f_inf and f_det:
                elements.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{f_det}", normal_text))
            elements.append(Spacer(1, 3))

    elements.append(Spacer(1, 10))

    # 7. Early Medical-Evaluation Guidance
    elements.append(Paragraph("4. Early Medical-Evaluation Guidance", section_heading))
    raw_recs = prediction_data.get("recommendations", [])
    
    # Filter out treatment, medication, exercise prescriptions, and fixed intervals
    safe_recs = []
    has_marker_rec = False
    has_followup_rec = False

    for r in raw_recs:
        r_lower = r.lower()
        if "exercise" in r_lower or "quadriceps" in r_lower or "strengthening" in r_lower or "radiographic" in r_lower or "treatment" in r_lower:
            continue
        if "3 to 6 months" in r_lower or "3-6 months" in r_lower:
            safe_recs.append("Follow-up screening may be considered based on symptoms and guidance from a qualified healthcare professional.")
            has_followup_rec = True
            continue
        safe_recs.append(r)
        if "risk markers were identified" in r_lower or "qualified healthcare professional" in r_lower:
            has_marker_rec = True

    if not safe_recs:
        safe_recs = [
            "OA-related risk markers were identified in this screening. Consider evaluation by a qualified healthcare professional for further assessment.",
            "Follow-up screening may be considered based on symptoms and guidance from a qualified healthcare professional."
        ]
    else:
        if not has_followup_rec:
            safe_recs.append("Follow-up screening may be considered based on symptoms and guidance from a qualified healthcare professional.")

    for r in safe_recs:
        elements.append(Paragraph(f"✓ {r}", normal_text))
        elements.append(Spacer(1, 2))

    elements.append(Spacer(1, 14))

    # 8. Prominent Medical Safety Disclaimer
    disclaimer_box = [
        [
            Paragraph(
                "<b>IMPORTANT MEDICAL DISCLAIMER:</b><br/>"
                "This report provides an AI-assisted preliminary screening indication based on available patient-reported and camera-derived information. "
                "It is not a clinical diagnosis and should not replace professional medical evaluation. "
                "DEVELOPMENT PROTOTYPE — MODEL TRAINED ON EXPERIMENTAL DATA — NOT FOR CLINICAL USE.",
                disclaimer_text
            )
        ]
    ]
    disc_table = Table(disclaimer_box, colWidths=[540])
    disc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#DC2626")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(disc_table)

    # Build Document
    doc.build(elements)
    print(f"[REPORT] Generated PDF report: {file_path}")
    return file_path
