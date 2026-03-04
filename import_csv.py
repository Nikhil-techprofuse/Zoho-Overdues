import pandas as pd
import re
from app import app
from models import db, Invoice

# ---------- LOAD CSV ----------
df = pd.read_csv("Zoho_Overdues_CLEAN.csv")

print("Detected Columns:")
print(df.columns)

# ---------- CLEAN COLUMN NAMES ----------
df.columns = df.columns.str.strip().str.lower()


# ---------- AGEING CLEANER ----------
def parse_ageing(value):
    """
    Converts:
    '>45 Days' -> 45
    '31-45 Days' -> 45
    '0-15 Days' -> 15
    """
    if pd.isna(value):
        return 0

    numbers = re.findall(r"\d+", str(value))

    if numbers:
        return int(numbers[-1])   

    return 0


# ---------- IMPORT ----------
with app.app_context():

    # clear old invoices
    Invoice.query.delete()

    for _, row in df.iterrows():

        invoice = Invoice(
            transaction_no=str(row["transaction#"]),
            customer=str(row["customer name"]),
            amount=float(row["amount"]),
            balance_due=float(row["balance due"]),
            start_date=str(row["start date"]),
            end_date=str(row["end date"]),
            ageing=parse_ageing(row["ageing"]),
            owner=str(row["owner"]).lower(),
            status=str(row["status"]).lower()
        )

        db.session.add(invoice)

    db.session.commit()

print(" CSV Imported Successfully")