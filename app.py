from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from models import db, User, Invoice, DailyUpload
import pandas as pd
import datetime
import os
import re

# =====================================================
# APP CONFIG
# =====================================================

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "secret123"

db.init_app(app)


# =====================================================
# DATABASE INITIALIZATION
# =====================================================

with app.app_context():
    db.create_all()

    # Create default users only once
    if not User.query.first():

        users = [
            User(username="admin", password="admin123", role="admin"),
            User(username="srilakshmi", password="owner123", role="owner"),
            User(username="sireesha", password="owner123", role="owner"),
            User(username="vamsi", password="owner123", role="owner"),
            User(username="vijay", password="owner123", role="owner"),
            User(username="shravya", password="owner123", role="owner"),
        ]

        db.session.add_all(users)
        db.session.commit()


# =====================================================
# HELPER — LOGIN REQUIRED CHECK
# =====================================================

def require_login():
    """Return True if user logged in else False"""
    return "user" in session and "role" in session


# =====================================================
# PAGE ROUTES
# =====================================================

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("upload_page"))
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    if not require_login():
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session.get("user", "User"), role=session.get("role", "user"))


@app.route("/customers-page")
def customers_page():
    if not require_login():
        return redirect(url_for("login"))
    return render_template("customers.html", username=session.get("user", "User"), role=session.get("role", "user"))


@app.route("/upload-page")
def upload_page():
    if not require_login():
        return render_template("index.html")
    return render_template("upload.html", username=session.get("user", "User"), role=session.get("role", "user"))


# =====================================================
# LOGIN API
# =====================================================

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(
        username=username,
        password=password
    ).first()

    if not user:
        return jsonify({"message": "Invalid credentials"}), 401

    # Store session
    session["user"] = user.username
    session["role"] = user.role

    return jsonify({
        "message": "Login successful",
        "user": user.username,
        "role": user.role
    }), 200


@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"success": True})


# =====================================================
# DASHBOARD DATA API
# =====================================================

@app.route("/dashboard-data")
def dashboard_data():

    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401

    role = session["role"]
    username = session["user"]

    query = DailyUpload.query

    # Owner restriction
    if role != "admin":
        query = query.filter_by(owner=username)

    invoices = query.all()

    total_value = sum(i.amount or 0 for i in invoices)
    total_due = sum(i.balance_due or 0 for i in invoices)
    total_invoices = len(invoices)
    unique_customers = len(set(i.customer_name for i in invoices if i.customer_name))

    return jsonify({
        "totalValue": total_value,
        "totalDue": total_due,
        "totalInvoices": total_invoices,
        "uniqueCustomers": unique_customers
    })


# =====================================================
# UNIQUE CUSTOMERS API
# =====================================================

@app.route("/customers-data")
def customers_data():

    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401

    role = session["role"]
    username = session["user"]

    query = DailyUpload.query

    if role != "admin":
        query = query.filter_by(owner=username)

    invoices = query.all()

    customers = {}

    for i in invoices:

        if not i.customer_name:
            continue

        if i.customer_name not in customers:
            customers[i.customer_name] = {
                "customer": i.customer_name,
                "total_due": 0,
                "invoices": []
            }

        customers[i.customer_name]["total_due"] += i.balance_due or 0

        customers[i.customer_name]["invoices"].append({
            "invoice": i.transaction_no,
            "amount": i.amount,
            "due": i.balance_due,
            "status": i.status,
            "owner": i.owner
        })

    return jsonify(list(customers.values()))

#--- AGENT WISE DATA ---

@app.route("/agent-page")
def agent_page():
    if not require_login():
        return render_template("index.html")
    return render_template("agent.html", username=session.get("user", "User"), role=session.get("role", "user"))

@app.route("/agent-data")
def agent_data():

    if not require_login():
        return jsonify({"error":"Unauthorized"}),401

    role = session["role"]
    username = session["user"]

    query = DailyUpload.query

    if role != "admin":
        query = query.filter_by(owner=username)

    invoices = query.all()

    agents = {}

    for i in invoices:

        if not i.owner:
            continue

        if i.owner not in agents:
            agents[i.owner] = {
                "owner": i.owner,
                "total_amount":0,
                "total_due":0,
                "invoice_count":0,
                "invoices":[]
            }

        agents[i.owner]["total_amount"] += i.amount or 0
        agents[i.owner]["total_due"] += i.balance_due or 0
        agents[i.owner]["invoice_count"] += 1

        agents[i.owner]["invoices"].append({
            "invoice": i.transaction_no,
            "customer": i.customer_name,
            "due": i.balance_due
        })

    return jsonify(list(agents.values()))


# --- UPLOAD API ---

def parse_ageing(value):
    if pd.isna(value):
        return 0
    numbers = re.findall(r"\d+", str(value))
    if numbers:
        return int(numbers[-1])
    return 0


@app.route("/upload", methods=["POST"])
def upload_file():

    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not (file.filename.endswith(".csv") or file.filename.endswith(".xlsx") or file.filename.endswith(".xls")):
        return jsonify({"error": "Invalid file format. Please upload CSV or Excel."}), 400

    # Save temp file
    temp_path = os.path.join("static", file.filename)
    file.save(temp_path)

    try:
        # Read file
        if file.filename.endswith(".csv"):
            df = pd.read_csv(temp_path)
        else:
            df = pd.read_excel(temp_path)

        # Basic cleaning
        df.columns = df.columns.str.strip().str.lower()
        
        # Column mapping check
        required_cols = ["transaction#", "customer name", "amount", "balance due", "start date", "end date", "ageing", "owner", "status"]
        # Basic check, we'll use .get() for safety
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Clear old daily data (daily refresh)
        DailyUpload.query.delete()

        # Helper to clean date strings from pandas
        def clean_dt(val):
            if pd.isna(val) or not val: return ""
            return str(val).split(" ")[0]

        upload_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for _, row in df.iterrows():
            # Check for Overdue in status or ageing
            status_val = str(row.get("status", "")).lower()
            ageing_val = str(row.get("ageing", ""))
            
            # Simple logic: if status is overdue, keep it. 
            # We will handle highlighting in the frontend via tags.

            daily_inv = DailyUpload(
                ageing=str(row.get("ageing", "")),
                date=clean_dt(row.get("date", "")),
                transaction_no=str(row.get("transaction#", "")),
                type=str(row.get("type", "")),
                status=status_val,
                customer_name=str(row.get("customer name", "")),
                age=float(row.get("age", 0)) if pd.notna(row.get("age")) else 0,
                amount=float(row.get("amount", 0)) if pd.notna(row.get("amount")) else 0,
                balance_due=float(row.get("balance due", 0)) if pd.notna(row.get("balance due")) else 0,
                owner=next((str(row[k]) for k in ["owner", "invoice owner", "agent", "customer owner"] if k in row), ""),
                domain_name=str(row.get("domain name", "")),
                payment_received_date="",
                start_date=clean_dt(row.get("start date", "")),
                end_date=clean_dt(row.get("end date", "")),
                upload_timestamp=upload_time
            )
            db.session.add(daily_inv)

        db.session.commit()
        os.remove(temp_path)

        return jsonify({"message": f"Successfully imported {len(df)} daily records!"}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"error": str(e)}), 500


@app.route("/uploaded-data")
def uploaded_data():
    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401

    invoices = DailyUpload.query.all()
    result = [{
        "id": i.id,
        "ageing": i.ageing,
        "date": i.date,
        "invoice": i.transaction_no,
        "type": i.type,
        "status": i.status,
        "customer": i.customer_name,
        "age": i.age,
        "amount": i.amount,
        "due": i.balance_due,
        "owner": i.owner,
        "domain": i.domain_name,
        "start": i.start_date,
        "end": i.end_date,
        "timestamp": i.upload_timestamp,
        "custom_status": i.custom_status or "Pending",
        "comments": i.comments or ""
    } for i in invoices]

    return jsonify(result)


@app.route("/update-record/<int:record_id>", methods=["PATCH"])
def update_record(record_id):
    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401

    role = session["role"]
    username = session["user"]

    record = DailyUpload.query.get(record_id)
    if not record:
        return jsonify({"error": "Record not found"}), 404

    # Non-admins can only update records assigned to them
    if role != "admin" and record.owner.lower() != username.lower():
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    if "custom_status" in data:
        record.custom_status = data["custom_status"]
    if "comments" in data:
        record.comments = data["comments"]

    db.session.commit()
    return jsonify({"message": "Updated successfully"}), 200


@app.route("/download-data")
def download_data():
    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401

    from flask import send_file
    import io

    role = session["role"]
    username = session["user"]

    query = DailyUpload.query
    if role != "admin":
        query = query.filter_by(owner=username)

    records = query.all()

    rows = [{
        "Ageing":             r.ageing,
        "Date":               r.date,
        "Transaction No":     r.transaction_no,
        "Type":               r.type,
        "Invoice Status":     r.status,
        "Customer Name":      r.customer_name,
        "Age (Days)":         r.age,
        "Amount":             r.amount,
        "Balance Due":        r.balance_due,
        "Owner":              r.owner,
        "Domain":             r.domain_name,
        "Start Date":         r.start_date,
        "End Date":           r.end_date,
        "Custom Status":      r.custom_status or "Pending",
        "Comments":           r.comments or "",
        "Upload Timestamp":   r.upload_timestamp,
    } for r in records]

    df = pd.DataFrame(rows)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Daily Data")
    output.seek(0)

    filename = f"daily_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )


# =====================================================
# RUN APP
# =====================================================

if __name__ == "__main__":
    app.run(debug=True)