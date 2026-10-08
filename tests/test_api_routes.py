import pytest
from backend.app.main import app
from backend.app.schemas import (
    ScreeningCreate,
    QuestionnaireInput,
    MovementSummaryInput,
    MovementFrameData,
    PredictionRequest
)
from backend.app.routes.screening import (
    predict_screening_risk,
    create_screening,
    analyze_movement
)
from backend.app.database import SessionLocal, engine, Base
from backend.app.models import Patient

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    # Ensure a test patient exists
    p = session.query(Patient).filter(Patient.patient_code == "UNIT-TEST-01").first()
    if not p:
        p = Patient(
            patient_code="UNIT-TEST-01",
            name="Unit Test Patient",
            age=55,
            gender="Female",
            activity_level="Moderate",
            joint_injury=0,
            family_history=1
        )
        session.add(p)
        session.commit()
        session.refresh(p)
    yield session
    session.close()

def test_api_valid_screening_and_prediction(db):
    patient = db.query(Patient).filter(Patient.patient_code == "UNIT-TEST-01").first()
    assert patient is not None

    q_input = QuestionnaireInput(
        knee_pain=2,
        joint_stiffness=2,
        walking_difficulty=1,
        stair_difficulty=2,
        standing_difficulty=1,
        knee_bending_difficulty=2,
        pain_increase_activity=2,
        pain_scale=4.5,
        mobility_scale=7.0
    )

    m_input = MovementSummaryInput(
        left_knee_rom=115.0,
        right_knee_rom=118.0,
        knee_symmetry=97.4,
        average_knee_angle=145.0,
        gait_symmetry=88.0,
        movement_consistency=85.0,
        posture_score=82.0,
        hip_movement=36.0,
        ankle_movement=26.0,
        movement_smoothness=86.0,
        assessment_status="VALID",
        landmark_quality_score=94.0,
        valid_frame_ratio=0.92,
        movement_duration=8.0,
        frames=[
            MovementFrameData(timestamp=100.0, left_knee_angle=90.0, right_knee_angle=115.0),
            MovementFrameData(timestamp=200.0, left_knee_angle=88.0, right_knee_angle=116.0)
        ]
    )

    # 1. Test Prediction Endpoint Handler
    pred_req = PredictionRequest(
        patient_id=patient.id,
        age=patient.age,
        activity_level="Moderate",
        joint_injury=0,
        family_history=1,
        questionnaire=q_input,
        movement=m_input
    )
    pred_res = predict_screening_risk(pred_req)
    assert pred_res["risk_level"] in ["Low Risk", "Moderate Risk", "High Risk"]
    assert 0 <= pred_res["risk_probability"] <= 100
    assert pred_res["assessment_status"] == "VALID"
    assert pred_res["model_name"] in ["LogisticRegression", "XGBoost"]

    # 2. Test Screening Creation Endpoint Handler
    scr_create = ScreeningCreate(
        patient_id=patient.id,
        questionnaire=q_input,
        movement=m_input,
        notes="Automated route test"
    )
    scr_res = create_screening(scr_create, db=db)
    assert scr_res["risk_level"] in ["Low Risk", "Moderate Risk", "High Risk"]
    assert scr_res["assessment_status"] == "VALID"
    assert scr_res["id"] is not None

def test_api_blocks_unreliable_camera_data(db):
    patient = db.query(Patient).filter(Patient.patient_code == "UNIT-TEST-01").first()
    assert patient is not None

    q_input = QuestionnaireInput(
        knee_pain=2,
        joint_stiffness=2,
        walking_difficulty=1,
        stair_difficulty=2,
        standing_difficulty=1,
        knee_bending_difficulty=2,
        pain_increase_activity=2,
        pain_scale=4.5,
        mobility_scale=7.0
    )

    # REPEAT_REQUIRED movement payload
    bad_movement = MovementSummaryInput(
        left_knee_rom=115.0,
        right_knee_rom=118.0,
        knee_symmetry=97.4,
        average_knee_angle=145.0,
        gait_symmetry=88.0,
        movement_consistency=85.0,
        posture_score=82.0,
        hip_movement=36.0,
        ankle_movement=26.0,
        movement_smoothness=86.0,
        assessment_status="REPEAT_REQUIRED",
        validation_message="Right ankle is not detected reliably. Please reposition and repeat."
    )

    # Must raise HTTPException 400
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        predict_screening_risk(PredictionRequest(
            patient_id=patient.id,
            age=patient.age,
            activity_level="Moderate",
            joint_injury=0,
            family_history=1,
            questionnaire=q_input,
            movement=bad_movement
        ))
    assert exc_info.value.status_code == 400
    assert "Unreliable camera data blocked" in str(exc_info.value.detail)

    with pytest.raises(HTTPException) as exc_create:
        create_screening(ScreeningCreate(
            patient_id=patient.id,
            questionnaire=q_input,
            movement=bad_movement
        ), db=db)
    assert exc_create.value.status_code == 400
