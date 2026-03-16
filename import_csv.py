"""
import_csv.py — One-time script to seed the database from Zoho_Overdues_CLEAN.csv.

Usage:
    python import_csv.py

Reads Zoho_Overdues_CLEAN.csv from the project root, clears old Invoice records,
and imports fresh data into the database.
"""
import pandas as pd
import re
from app import app
from models import db, DailyUpload

# ---------- LOAD CSV ----------
df = pd.read_csv("Zoho_Overdues_CLEAN.csv")

print("Detected Columns:")
print(df.columns.tolist())

# ---------- CLEAN COLUMN NAMES ----------
df.columns = df.columns.str.strip().str.lower()


# ---------- AGEING CLEANER ----------
def parse_ageing(value):
    """
    Converts ageing strings to numeric upper bound:
      '>45 Days'   -> 45
      '31-45 Days' -> 45
      '0-15 Days'  -> 15
    """
    if pd.isna(value):
        return 0
    numbers = re.findall(r"\d+", str(value))
    return int(numbers[-1]) if numbers else 0


# ---------- IMPORT ----------
with app.app_context():
    # Clear old data
    DailyUpload.query.delete()

    for _, row in df.iterrows():
        record = DailyUpload(
            transaction_no=str(row.get("transaction#", "")),
            customer_name =str(row.get("customer name", "")),
            amount        =float(row.get("amount", 0) or 0),
            balance_due   =float(row.get("balance due", 0) or 0),
            start_date    =str(row.get("start date", "")),
            end_date      =str(row.get("end date", "")),
            ageing        =str(row.get("ageing", "")),
            age           =parse_ageing(row.get("ageing", "")),
            owner         =str(row.get("owner", "")).lower(),
            status        =str(row.get("status", "")).lower(),
            change_flag   ="new",
            is_active     =1,
        )
        db.session.add(record)

    db.session.commit()

print("CSV imported successfully.")
