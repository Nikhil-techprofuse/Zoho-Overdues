import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
if not os.path.exists(db_path):
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE daily_upload ADD COLUMN change_flag VARCHAR(20) DEFAULT 'new'")
    print("Added change_flag column.")
except Exception as e:
    print(f"change_flag already exists or error: {e}")

try:
    cursor.execute("ALTER TABLE daily_upload ADD COLUMN is_active BOOLEAN DEFAULT 1")
    print("Added is_active column.")
except Exception as e:
    print(f"is_active already exists or error: {e}")

# Set all existing records to 'unchanged' and active
cursor.execute("UPDATE daily_upload SET change_flag='unchanged', is_active=1 WHERE change_flag IS NULL OR change_flag=''")
print(f"Updated {cursor.rowcount} existing rows to 'unchanged'.")

conn.commit()
conn.close()
print('Migration complete')
