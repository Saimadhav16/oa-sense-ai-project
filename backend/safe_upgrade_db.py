import sqlite3
import datetime

db_path = "oa-sense-ai/backend/data/oasense.db"
con = sqlite3.connect(db_path)
cur = con.cursor()

def add_column_if_missing(table, column, col_type):
    cur.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cur.fetchall()]
    if column not in columns:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"Added column {column} ({col_type}) to table {table}")
    else:
        print(f"Column {column} already exists in {table}")

# Add columns to patients
add_column_if_missing("patients", "doctor_notes", "TEXT")
add_column_if_missing("patients", "referral_info", "TEXT")
add_column_if_missing("patients", "follow_up_instructions", "TEXT")
add_column_if_missing("patients", "updated_at", "DATETIME")

# Add columns to screenings
add_column_if_missing("screenings", "confidence_level", "VARCHAR(20)")
add_column_if_missing("screenings", "data_quality", "VARCHAR(20)")
add_column_if_missing("screenings", "confidence_reason", "TEXT")
add_column_if_missing("screenings", "updated_at", "DATETIME")

# Create patient_qr_access if missing
cur.execute("""
CREATE TABLE IF NOT EXISTS patient_qr_access (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT 0,
    access_count INTEGER NOT NULL DEFAULT 0,
    last_accessed_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
)
""")
cur.execute("CREATE INDEX IF NOT EXISTS ix_patient_qr_access_token_hash ON patient_qr_access(token_hash)")

# Create audit_logs if missing
cur.execute("""
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(60) NOT NULL,
    patient_id INTEGER,
    assessment_id INTEGER,
    status VARCHAR(30) NOT NULL DEFAULT 'SUCCESS',
    source_ip VARCHAR(45),
    details TEXT
)
""")
cur.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_timestamp ON audit_logs(timestamp)")
cur.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs(action)")
cur.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_patient_id ON audit_logs(patient_id)")

# Create sync_records if missing
cur.execute("""
CREATE TABLE IF NOT EXISTS sync_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type VARCHAR(40) NOT NULL,
    entity_id INTEGER NOT NULL,
    sync_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    payload_json TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    synced_at DATETIME
)
""")
cur.execute("CREATE INDEX IF NOT EXISTS ix_sync_records_sync_status ON sync_records(sync_status)")

con.commit()
con.close()
print("Safe database upgrade executed successfully.")
