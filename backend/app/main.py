import os
import json
import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import engine, Base, SessionLocal
from .models import User, Patient, Screening, Report
from .auth import seed_demo_user
from .routes import auth, patients, screening, reports, dashboard
from .ml.pose_analysis import calculate_knee_angles, analyze_posture
from .ml.gait_analysis import analyze_gait_time_series
from .ml.model import load_ml_model

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="OA-Sense AI API",
    description="AI-Assisted Early Osteoarthritis Risk Screening System (Research / Demo Prototype). Not for clinical diagnosis.",
    version="1.0.0"
)

# Enable CORS for frontend Vite dev server and production origins
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()] if allowed_origins_env != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(screening.router)
app.include_router(reports.router)
app.include_router(dashboard.router)

# Ensure reports directory exists
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def seed_initial_demo_patients():
    """Seeds initial demonstration patient profiles and screening sessions for immediate dashboard visibility."""
    db = SessionLocal()
    try:
        seed_demo_user(db)
        if db.query(Patient).count() == 0:
            demo_patients_data = [
                {
                    "patient_code": "OA-2026-1042",
                    "name": "Ramesh Kumar Sharma",
                    "age": 58,
                    "gender": "Male",
                    "phone": "+91 98765 43210",
                    "location": "Jaipur Rural Camp",
                    "occupation": "Agricultural Laborer",
                    "activity_level": "High",
                    "joint_injury": 1,
                    "family_history": 1,
                    "demanding_work": 1,
                    "walking_difficulty": 3,
                    "stair_difficulty": 3,
                    "morning_stiffness": 3,
                    "risk": "High Risk",
                    "prob": 82.5,
                    "pain": 7.5,
                    "mobility": 3.8,
                    "left_rom": 88.0,
                    "right_rom": 118.0,
                    "gait_sym": 71.2,
                    "posture": 68.0
                },
                {
                    "patient_code": "OA-2026-1043",
                    "name": "Sunita Devi",
                    "age": 52,
                    "gender": "Female",
                    "phone": "+91 98123 45678",
                    "location": "Alwar Primary Health Centre",
                    "occupation": "Homemaker / Weaver",
                    "activity_level": "Moderate",
                    "joint_injury": 0,
                    "family_history": 1,
                    "demanding_work": 1,
                    "walking_difficulty": 2,
                    "stair_difficulty": 2,
                    "morning_stiffness": 2,
                    "risk": "Moderate Risk",
                    "prob": 54.0,
                    "pain": 4.5,
                    "mobility": 6.2,
                    "left_rom": 112.0,
                    "right_rom": 115.0,
                    "gait_sym": 84.5,
                    "posture": 78.0
                },
                {
                    "patient_code": "OA-2026-1044",
                    "name": "Anil Verma",
                    "age": 39,
                    "gender": "Male",
                    "phone": "+91 94111 22233",
                    "location": "Community Center",
                    "occupation": "Teacher",
                    "activity_level": "Light",
                    "joint_injury": 0,
                    "family_history": 0,
                    "demanding_work": 0,
                    "walking_difficulty": 0,
                    "stair_difficulty": 0,
                    "morning_stiffness": 0,
                    "risk": "Low Risk",
                    "prob": 14.2,
                    "pain": 1.0,
                    "mobility": 9.5,
                    "left_rom": 136.0,
                    "right_rom": 138.0,
                    "gait_sym": 96.0,
                    "posture": 92.0
                }
            ]

            for d in demo_patients_data:
                patient = Patient(
                    patient_code=d["patient_code"],
                    name=d["name"],
                    age=d["age"],
                    gender=d["gender"],
                    phone=d["phone"],
                    location=d["location"],
                    occupation=d["occupation"],
                    activity_level=d["activity_level"],
                    joint_injury=d["joint_injury"],
                    family_history=d["family_history"],
                    demanding_work=d["demanding_work"],
                    walking_difficulty=d["walking_difficulty"],
                    stair_difficulty=d["stair_difficulty"],
                    morning_stiffness=d["morning_stiffness"],
                    created_at=datetime.datetime.utcnow() - datetime.timedelta(days=2)
                )
                db.add(patient)
                db.commit()
                db.refresh(patient)

                screening = Screening(
                    patient_id=patient.id,
                    pain_score=d["pain"],
                    stiffness_score=2.0 if d["risk"] != "Low Risk" else 0.0,
                    mobility_score=d["mobility"],
                    left_knee_rom=d["left_rom"],
                    right_knee_rom=d["right_rom"],
                    knee_symmetry=round(100.0 - abs(d["left_rom"] - d["right_rom"]), 1),
                    average_knee_angle=round((d["left_rom"] + d["right_rom"]) / 2.0, 1),
                    gait_symmetry=d["gait_sym"],
                    movement_consistency=d["gait_sym"],
                    posture_score=d["posture"],
                    movement_smoothness=88.0,
                    risk_level=d["risk"],
                    risk_probability=d["prob"],
                    confidence=92.0,
                    questionnaire_contribution=52.0,
                    movement_contribution=48.0,
                    sync_status="synced",
                    model_version="1.0.0-demo",
                    created_at=datetime.datetime.utcnow() - datetime.timedelta(days=1)
                )
                db.add(screening)
                db.commit()

            print("[INIT] Seeded initial demonstration patients and screening records.")
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    print("[SYSTEM] Starting OA-Sense AI Backend Engine...")
    load_ml_model()
    seed_initial_demo_patients()

@app.get("/")
def read_root():
    return {
        "system": "OA-Sense AI",
        "title": "AI-Assisted Early Osteoarthritis Risk Screening System",
        "status": "online",
        "mode": "DEMO / RESEARCH PROTOTYPE",
        "disclaimer": "This system provides preliminary risk assessment and is strictly NOT a medical diagnosis.",
        "documentation": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()}

# --- Real-Time Movement Analysis WebSocket Endpoint ---
@app.websocket("/ws/movement-analysis")
async def websocket_movement_analysis(websocket: WebSocket):
    await websocket.accept()
    session_frames = []

    try:
        while True:
            text_data = await websocket.receive_text()
            try:
                msg = json.loads(text_data)
            except Exception:
                continue

            event_type = msg.get("type", "frame")

            if event_type == "frame":
                landmarks = msg.get("landmarks", {})
                timestamp = msg.get("timestamp", 0.0)

                # 1. Joint angles
                angles = calculate_knee_angles(landmarks)
                left_angle = angles["left_knee_angle"]
                right_angle = angles["right_knee_angle"]

                # 2. Posture metrics
                posture = analyze_posture(landmarks)

                # Store running frame window
                frame_entry = {
                    "timestamp": timestamp,
                    "left_knee_angle": left_angle,
                    "right_knee_angle": right_angle,
                    "posture_value": posture.get("posture_score", 85.0)
                }
                session_frames.append(frame_entry)
                if len(session_frames) > 300:  # keep last 300 frames (~10 sec at 30fps)
                    session_frames.pop(0)

                # 3. Rolling gait metrics
                gait_metrics = analyze_gait_time_series(session_frames[-45:])

                # Determine movement state
                vel = 0.0
                if len(session_frames) >= 2:
                    prev = session_frames[-2]
                    vel = abs(left_angle - prev["left_knee_angle"]) + abs(right_angle - prev["right_knee_angle"])
                
                movement_status = "ACTIVE" if vel > 3.0 else "STATIONARY"

                response = {
                    "type": "analysis_feedback",
                    "left_knee_angle": left_angle,
                    "right_knee_angle": right_angle,
                    "movement_status": movement_status,
                    "posture_score": posture.get("posture_score", 85.0),
                    "posture_rating": posture.get("posture_rating", "Optimal"),
                    "gait_symmetry": gait_metrics.get("gait_symmetry", 90.0),
                    "cadence_estimate": gait_metrics.get("cadence_estimate", 90.0),
                    "movement_smoothness": gait_metrics.get("movement_smoothness", 90.0),
                    "analysis_status": "TRACKING_ACTIVE"
                }
                await websocket.send_text(json.dumps(response))

            elif event_type == "reset":
                session_frames.clear()
                await websocket.send_text(json.dumps({"type": "reset_ack", "status": "READY"}))

            elif event_type == "summary_request":
                summary = analyze_gait_time_series(session_frames)
                await websocket.send_text(json.dumps({"type": "session_summary", "metrics": summary}))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WS ERROR] {e}")
