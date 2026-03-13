from app import app, db
from models import DailyUpload
import pandas as pd
from datetime import datetime, date

def clean_date_migration(val):
    if not val or str(val).strip() == "":
        return ""
    try:
        # If it's already a date object
        if isinstance(val, (datetime, date)):
            return val.strftime("%Y-%m-%d")
        
        # Try parsing string
        dt = pd.to_datetime(val, dayfirst=True, errors='coerce')
        if pd.notna(dt):
            return dt.strftime("%Y-%m-%d")
    except:
        pass
    return str(val).strip().split(" ")[0]

with app.app_context():
    print("Starting date normalization migration...")
    records = DailyUpload.query.all()
    count = 0
    for r in records:
        updated = False
        
        new_date = clean_date_migration(r.date)
        if new_date != r.date:
            r.date = new_date
            updated = True
            
        new_start = clean_date_migration(r.start_date)
        if new_start != r.start_date:
            r.start_date = new_start
            updated = True
            
        new_end = clean_date_migration(r.end_date)
        if new_end != r.end_date:
            r.end_date = new_end
            updated = True
            
        if updated:
            count += 1
            
    db.session.commit()
    print(f"Migration complete. Updated {count} records.")
