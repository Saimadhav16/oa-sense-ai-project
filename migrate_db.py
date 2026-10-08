import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "backend", "data", "oasense.db")
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(screenings)")
    cols = [r[1] for r in cur.fetchall()]
    new_cols = [
        ("assessment_status", "TEXT DEFAULT 'VALID'"),
        ("landmark_quality_score", "REAL DEFAULT 100.0"),
        ("valid_frame_ratio", "REAL DEFAULT 1.0"),
        ("movement_quality_score", "REAL DEFAULT 100.0"),
        ("validation_message", "TEXT"),
        ("min_left_knee_angle", "REAL"),
        ("max_left_knee_angle", "REAL"),
        ("mean_left_knee_angle", "REAL"),
        ("median_left_knee_angle", "REAL"),
        ("min_right_knee_angle", "REAL"),
        ("max_right_knee_angle", "REAL"),
        ("mean_right_knee_angle", "REAL"),
        ("median_right_knee_angle", "REAL"),
        ("rom_difference", "REAL"),
        ("peak_left_velocity", "REAL"),
        ("peak_right_velocity", "REAL"),
        ("movement_duration", "REAL"),
        ("repetition_count", "INTEGER"),
        ("movement_tests_json", "TEXT"),
        ("model_name", "TEXT DEFAULT 'XGBoost'"),
        ("prediction_status", "TEXT DEFAULT 'COMPLETED'")
    ]
    for col_name, col_type in new_cols:
        if col_name not in cols:
            cur.execute(f"ALTER TABLE screenings ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name} to screenings")

    cur.execute("PRAGMA table_info(movement_frames)")
    mf_cols = [r[1] for r in cur.fetchall()]
    if "movement_type" not in mf_cols:
        cur.execute("ALTER TABLE movement_frames ADD COLUMN movement_type TEXT DEFAULT 'KNEE_FLEXION'")
        print("Added movement_type to movement_frames")
    if "frame_valid" not in mf_cols:
        cur.execute("ALTER TABLE movement_frames ADD COLUMN frame_valid BOOLEAN DEFAULT 1")
        print("Added frame_valid to movement_frames")
    if "phase" not in mf_cols:
        cur.execute("ALTER TABLE movement_frames ADD COLUMN phase TEXT")
        print("Added phase to movement_frames")

    conn.commit()
    conn.close()
    print("Database migration successfully applied!")
