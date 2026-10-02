import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_root_and_health():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["system"] == "OA-Sense AI"

    res_h = client.get("/health")
    assert res_h.status_code == 200
    assert res_h.json()["status"] == "healthy"

def test_demo_login():
    res = client.post("/api/auth/login", json={"email": "demo@oasense.ai", "password": "demo123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "healthcare_worker"

def test_patient_creation_and_listing():
    patient_payload = {
        "patient_code": "TEST-OA-01",
        "name": "Pooja Patel",
        "age": 48,
        "gender": "Female",
        "phone": "+91 99887 76655",
        "location": "Outreach Clinic A",
        "occupation": "Artisan",
        "activity_level": "Moderate",
        "joint_injury": 0,
        "family_history": 1,
        "demanding_work": 0,
        "walking_difficulty": 1,
        "stair_difficulty": 2,
        "morning_stiffness": 1
    }
    res = client.post("/api/patients", json=patient_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Pooja Patel"
    patient_id = data["id"]

    # Retrieve patient list
    list_res = client.get("/api/patients")
    assert list_res.status_code == 200
    assert len(list_res.json()) > 0

    # Retrieve patient detail
    detail_res = client.get(f"/api/patients/{patient_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["patient"]["name"] == "Pooja Patel"

def test_screening_and_prediction_flow():
    # First get or create a patient
    res_p = client.get("/api/patients")
    patient = res_p.json()[0]

    screening_payload = {
        "patient_id": patient["id"],
        "questionnaire": {
            "knee_pain": 2,
            "joint_stiffness": 2,
            "walking_difficulty": 1,
            "stair_difficulty": 2,
            "standing_difficulty": 1,
            "knee_bending_difficulty": 2,
            "pain_increase_activity": 2,
            "pain_scale": 4.5,
            "mobility_scale": 7.0
        },
        "movement": {
            "left_knee_rom": 115.0,
            "right_knee_rom": 118.0,
            "knee_symmetry": 97.4,
            "average_knee_angle": 145.0,
            "gait_symmetry": 88.0,
            "movement_consistency": 85.0,
            "posture_score": 82.0,
            "hip_movement": 36.0,
            "ankle_movement": 26.0,
            "movement_smoothness": 86.0
        },
        "notes": "Automated integration test screening"
    }

    res_scr = client.post("/api/screenings", json=screening_payload)
    assert res_scr.status_code == 200
    scr_data = res_scr.json()
    assert scr_data["risk_level"] in ["Low Risk", "Moderate Risk", "High Risk"]
    screening_id = scr_data["id"]

    # Generate PDF report for this screening
    rep_res = client.post("/api/reports/generate", json={"screening_id": screening_id})
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert "report_id" in rep_data

    # Download report
    down_res = client.get(f"/api/reports/{rep_data['report_id']}")
    assert down_res.status_code == 200
    assert down_res.headers["content-type"] == "application/pdf"

def test_dashboard_statistics():
    res = client.get("/api/dashboard/statistics")
    assert res.status_code == 200
    stats = res.json()
    assert "total_patients" in stats
    assert "risk_distribution" in stats
    assert stats["total_patients"] > 0
