import os
import datetime
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

    q_cont = prediction_data.get("questionnaire_contribution", screening_data.get("questionnaire_contribution", 50.0))
    m_cont = prediction_data.get("movement_contribution", screening_data.get("movement_contribution", 50.0))

    risk_box_data = [
        [
            Paragraph(f"<b>SCREENING RESULT:</b> <br/><font size=16>{risk_level.upper()}</font>", risk_style),
            Paragraph(
                f"<b>Risk Indicator:</b> {risk_prob}%<br/>"
                f"<b>Model Confidence:</b> {conf}%<br/>"
                f"<b>Questionnaire Weight:</b> {q_cont}% | <b>Movement Weight:</b> {m_cont}%",
                normal_text
            )
        ]
    ]

    risk_box_table = Table(risk_box_data, colWidths=[240, 300])
    risk_box_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), risk_bg),
        ('BOX', (0, 0), (-1, -1), 1.5, risk_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(risk_box_table)
    elements.append(Spacer(1, 14))

    # 4. Biomechanical & Movement Results
    elements.append(Paragraph("1. Computer-Vision Movement Analysis", section_heading))
    
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
            Paragraph("Slight reduction" if left_rom < 110 else "Adequate", normal_text)
        ],
        [
            Paragraph("Right Knee Range of Motion", normal_text),
            Paragraph(f"{right_rom}°", normal_text),
            Paragraph("125° - 145°", normal_text),
            Paragraph("Slight reduction" if right_rom < 110 else "Adequate", normal_text)
        ],
        [
            Paragraph("Knee ROM Bilateral Symmetry", normal_text),
            Paragraph(f"{knee_sym}%", normal_text),
            Paragraph("&ge; 90%", normal_text),
            Paragraph("Asymmetry flagged" if knee_sym < 85 else "Balanced", normal_text)
        ],
        [
            Paragraph("Gait Symmetry Index", normal_text),
            Paragraph(f"{gait_sym}%", normal_text),
            Paragraph("&ge; 88%", normal_text),
            Paragraph("Step disparity detected" if gait_sym < 80 else "Normal symmetry", normal_text)
        ],
        [
            Paragraph("Posture Alignment Score", normal_text),
            Paragraph(f"{posture_val}/100", normal_text),
            Paragraph("&ge; 85/100", normal_text),
            Paragraph("Minor pelvic/trunk tilt" if posture_val < 75 else "Optimal alignment", normal_text)
        ],
        [
            Paragraph("Movement Smoothness", normal_text),
            Paragraph(f"{smoothness}%", normal_text),
            Paragraph("&ge; 85%", normal_text),
            Paragraph("Increased jerk/hesitation" if smoothness < 75 else "Smooth transition", normal_text)
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

    # 6. Top Risk Indicators & Explainability
    elements.append(Paragraph("3. Explainable Risk Factors (Model Drivers)", section_heading))
    top_factors = prediction_data.get("top_risk_factors", [])
    if not top_factors:
        elements.append(Paragraph("• No severe abnormal movement or pain markers detected in this screening session.", normal_text))
    else:
        for tf in top_factors[:4]:
            f_name = tf.get("factor", "Factor")
            f_stat = tf.get("status", "Info")
            f_det = tf.get("detail", "")
            elements.append(Paragraph(f"• <b>{f_name}</b> [{f_stat}]: {f_det}", normal_text))
            elements.append(Spacer(1, 2))

    elements.append(Spacer(1, 10))

    # 7. Recommendations
    elements.append(Paragraph("4. Clinical Recommendations & Follow-Up", section_heading))
    recs = prediction_data.get("recommendations", [
        "Consult with a licensed orthopedic specialist or primary care physician.",
        "Engage in joint-friendly low-impact physical exercise and quad strengthening.",
        "Perform follow-up screening in 3-6 months to assess progression."
    ])
    for r in recs:
        elements.append(Paragraph(f"✓ {r}", normal_text))
        elements.append(Spacer(1, 2))

    elements.append(Spacer(1, 14))

    # 8. Prominent Medical Safety Disclaimer
    disclaimer_box = [
        [
            Paragraph(
                "<b>IMPORTANT MEDICAL DISCLAIMER:</b><br/>"
                "Prototype screening result. This system is intended for preliminary risk screening and is not a medical diagnosis or a replacement for professional clinical evaluation or medical imaging. "
                "DEMO MODEL — TRAINED/TESTED USING SYNTHETIC DATA — NOT FOR CLINICAL USE.",
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
