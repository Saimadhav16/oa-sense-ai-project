import sqlite3

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

add_column_if_missing("screenings", "quality_report_json", "TEXT")
add_column_if_missing("screenings", "early_guidance", "TEXT")
add_column_if_missing("screenings", "confidence_breakdown_json", "TEXT")

con.commit()
con.close()
print("Quality gate schema migration completed successfully.")
