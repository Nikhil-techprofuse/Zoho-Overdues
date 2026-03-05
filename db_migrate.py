import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
if not os.path.exists(db_path):
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE daily_upload ADD COLUMN custom_status VARCHAR(50) DEFAULT 'Pending'")
except Exception as e:
    print(f"custom_status already exists or error: {e}")

try:
    cursor.execute("ALTER TABLE daily_upload ADD COLUMN comments TEXT DEFAULT ''")
except Exception as e:
    print(f"comments already exists or error: {e}")

conn.commit()
conn.close()
print('Added columns successfully')
