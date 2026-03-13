from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from models import db, User, Invoice, DailyUpload, UploadHistory
import pandas as pd
import datetime
from datetime import datetime, date   
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

# Global for debugging sheet names
last_sheets_debug = []

@app.route("/debug-sheets")
def debug_sheets():
    return jsonify({"sheets": last_sheets_debug})


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


@app.route("/uploads-history-page")
def uploads_history_page():
    if not require_login():
        return render_template("index.html")
    return render_template("uploads_history.html", username=session.get("user", "User"), role=session.get("role", "user"))


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

@app.route("/upload-history")
def get_upload_history():
    if not require_login():
        return jsonify({"message": "Unauthorized"}), 401
    history = UploadHistory.query.order_by(UploadHistory.id.desc()).limit(10).all()
    results = [
        {
            "id": h.id,
            "filename": h.filename,
            "date": h.upload_date,
            "stats": h.stats,
            "user": h.user
        } for h in history
    ]
    return jsonify(results)



# =====================================================
# DASHBOARD PAGE & DATA API
# =====================================================

@app.route("/dashboard")
def dashboard():
    if not require_login():
        return redirect(url_for("home"))
    return render_template("dashboard.html", username=session.get("user", "User"), role=session.get("role", "user"))

@app.route("/dashboard-data")
def dashboard_data():
    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401

    role = session["role"]
    username = session["user"]

    query = DailyUpload.query.filter_by(is_active=True)

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

    query = DailyUpload.query.filter_by(is_active=True)

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
    if session.get("role") != "admin":
        return jsonify({"error": "Access denied. Admins only."}), 403
    return render_template("agent.html", username=session.get("user", "User"), role=session.get("role", "user"))

@app.route("/agent-data")
def agent_data():

    if not require_login():
        return jsonify({"error":"Unauthorized"}),401
    
    if session.get("role") != "admin":
        return jsonify({"error": "Access denied. Admins only."}), 403

    role = session["role"]
    username = session["user"]

    query = DailyUpload.query.filter_by(is_active=True)

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
    
    # Only admins can upload files
    if session.get("role") != "admin":
        return jsonify({"error": "Access denied. Admins only."}), 403

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filename = file.filename.lower()

    if not (filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")):
        return jsonify({"error": "Upload CSV or Excel file"}), 400

    temp_path = os.path.join("static", filename)
    file.save(temp_path)


    try:

        # ===============================
        # READ FILE (CSV OR EXCEL)
        # ===============================
        if filename.endswith(".csv"):
            df = pd.read_csv(temp_path, encoding="utf-8", engine="python")
        else:
            # --- SMART SHEET SELECTION ---
            with pd.ExcelFile(temp_path) as xls:
                global last_sheets_debug
                last_sheets_debug = xls.sheet_names
                best_sheet = None
                max_recent_date = None

                for sheet_name in xls.sheet_names:
                    # Read 5 rows to check headers and some data
                    temp_df = pd.read_excel(xls, sheet_name=sheet_name, nrows=5)
                    norm_cols = [str(c).strip().lower().replace(" ", "_").replace("#", "") for c in temp_df.columns]
                    
                    if any(x in norm_cols for x in ["transaction", "invoice", "txn_no", "invoice_no"]):
                        # This is a candidate. Now check for "recency"
                        # Try to find a date column
                        date_col = next((c for c in temp_df.columns if "date" in str(c).lower()), None)
                        current_max_date = None
                        
                        if date_col:
                            try:
                                # Read the whole date column to find max
                                full_dates = pd.read_excel(xls, sheet_name=sheet_name, usecols=[date_col])
                                parsed_dates = pd.to_datetime(full_dates.iloc[:,0], errors='coerce').dropna()
                                if not parsed_dates.empty:
                                    current_max_date = parsed_dates.max()
                            except:
                                pass
                        
                        # Heuristic: Pick the one with the LATEST date, or the LAST one if tied
                        if best_sheet is None or (current_max_date and (max_recent_date is None or current_max_date >= max_recent_date)):
                            best_sheet = sheet_name
                            max_recent_date = current_max_date
                
                if best_sheet:
                    print(f"DEBUG: Smart selection (recency) found data in sheet -> {best_sheet} (Max Date: {max_recent_date})")
                    df = pd.read_excel(xls, sheet_name=best_sheet)
                else:
                    # Fallback to behavior before (first sheet)
                    df = pd.read_excel(temp_path)

        # ===============================
        # NORMALIZE COLUMN NAMES
        # ===============================
        print(f"DEBUG: Original columns -> {list(df.columns.values)}")
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
            .str.replace("#", "")
            .str.replace("-", "_")
            .str.replace(".", "")
            .str.replace("(", "")
            .str.replace(")", "")
        )
        print(f"DEBUG: Normalized columns -> {list(df.columns)}")
        print(f"DEBUG: Total rows in sheet -> {len(df)}")

        # Example conversions:
        # Transaction# → transaction
        # Customer Name → customer_name
        # Balance Due → balance_due
        # Domain name → domain_name
        
        print(f"DEBUG: Normalized columns -> {list(df.columns)}")
        print(f"DEBUG: Total rows in sheet -> {len(df)}")

        # ===============================
        # DATE CLEANER
        # ===============================
        def clean_date(val):
            if pd.isna(val) or str(val).strip() == "":
                return ""

            if isinstance(val, (datetime, date)):
                return val.strftime("%Y-%m-%d")

            # Try to parse string dates if they are not already in ISO format
            try:
                # First try pd.to_datetime which is quite smart
                dt = pd.to_datetime(val, dayfirst=True, errors='coerce')
                if pd.notna(dt):
                    return dt.strftime("%Y-%m-%d")
            except:
                pass

            return str(val).strip().split(" ")[0]
        
        # ===============================
        # CURRENCY CLEANER
        # ===============================
        def clean_amount(val):
            if pd.isna(val):
                return 0.0

            val = str(val)

            val = val.replace("₹", "")
            val = val.replace(",", "")
            val = val.strip()

            try:
                return float(val)
            except:
                return 0.0
        
        # ── STEP 1: Load all existing records keyed by transaction_no (Normalized) ──
        existing_records = {str(r.transaction_no).strip().upper(): r for r in DailyUpload.query.all()}
        existing_invoices = set(existing_records.keys())

        # ── STEP 2: Track which transaction_nos appear in the new sheet ──
        new_sheet_txns = set()
        stats = {"added": 0, "updated": 0, "unchanged": 0, "removed": 0}

        upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for idx, row in df.iterrows():
            # Support common variants for the Transaction/Invoice ID
            txn = str(
                row.get("transaction") or 
                row.get("transaction_no") or 
                row.get("transaction_number") or
                row.get("transaction_") or
                row.get("invoice") or
                row.get("invoice_no") or
                row.get("invoice_number") or
                row.get("invoice_id") or
                row.get("invoice_") or
                row.get("txn") or
                row.get("sl_no") or
                ""
            ).strip().upper()

            # Targeted Debug
            if any(x in str(txn) for x in ["260199", "260200", "26020000"]):
                print(f"!!! TARGET REACHED !!! Found {txn} in row {idx}")

            if not txn or str(txn).lower() == "nan":
                continue

            new_sheet_txns.add(txn)

            # Parse values from the sheet using normalized column names (with fallback aliases)
            ageing_val   = str(row.get("ageing") or row.get("ageing_group") or "")
            date_val     = clean_date(row.get("date") or row.get("invoice_date") or row.get("inv_date") or "")
            type_val     = str(row.get("type") or row.get("inv_type") or "")
            status_val   = str(row.get("status") or row.get("payment_status") or "").lower()
            customer_val = str(row.get("customer_name") or row.get("customer") or row.get("name") or "")
            age_val      = float(row.get("age", 0)) if pd.notna(row.get("age")) else 0
            amount_val   = clean_amount(row.get("amount") or row.get("total_amount") or row.get("invoice_amount") or row.get("total") or 0)
            due_val      = clean_amount(row.get("balance_due") or row.get("due") or row.get("pending") or row.get("balance") or 0)
            
            # Flexible owner lookup
            owner_val = str(
                row.get("owner") or 
                row.get("invoice_owner") or 
                row.get("agent") or 
                row.get("customer_owner") or 
                row.get("assigned_to") or
                ""
            ).lower()
            domain_val   = str(row.get("domain_name") or row.get("domain") or "")
            start_val    = clean_date(row.get("start_date") or row.get("start") or "")
            end_val      = clean_date(row.get("end_date") or row.get("end") or "")

            # Logic: Skip or Update if exists
            if txn in existing_invoices:
                rec = existing_records[txn]

                # Compare fields to see if "Update" is needed
                changed = (
                    abs(rec.amount - amount_val) > 0.01 or
                    abs(rec.balance_due - due_val) > 0.01 or
                    rec.ageing != ageing_val or
                    rec.status != status_val or
                    rec.customer_name != customer_val
                )

                if changed:
                    # Update fields but PRESERVE comments and custom_status
                    rec.ageing        = ageing_val
                    rec.date          = date_val
                    rec.type          = type_val
                    rec.status        = status_val
                    rec.customer_name = customer_val
                    rec.age           = age_val
                    rec.amount        = amount_val
                    rec.balance_due   = due_val
                    rec.owner         = owner_val
                    rec.domain_name   = domain_val
                    rec.start_date    = start_val
                    rec.end_date      = end_val
                    rec.upload_timestamp = upload_time
                    rec.change_flag   = "updated"
                    rec.is_active     = True
                    stats["updated"] += 1
                else:
                    # Mark unchanged but keep it visible
                    rec.change_flag = "unchanged"
                    rec.is_active   = True
                    stats["unchanged"] += 1

            else:
                # ── NEW: insert a fresh record ──
                new_rec = DailyUpload(
                    ageing           = ageing_val,
                    date             = date_val,
                    transaction_no   = txn,
                    type             = type_val,
                    status           = status_val,
                    customer_name    = customer_val,
                    age              = age_val,
                    amount           = amount_val,
                    balance_due      = due_val,
                    owner            = owner_val,
                    domain_name      = domain_val,
                    payment_received_date = "",
                    start_date       = start_val,
                    end_date         = end_val,
                    upload_timestamp = upload_time,
                    custom_status    = "Pending",
                    comments         = "",
                    change_flag      = "new",
                    is_active        = True
                )
                db.session.add(new_rec)
                stats["added"] += 1

        # ── STEP 3: Mark records missing from new sheet as "removed" ──
        print(f"DEBUG: Unique TXNs in sheet -> {len(new_sheet_txns)}")
        print(f"DEBUG: Existing active records -> {len([r for r in existing_records.values() if r.is_active])}")
        
        removed_count = 0
        for txn, rec in existing_records.items():
            if txn not in new_sheet_txns:
                rec.change_flag = "removed"
                rec.is_active   = False
                stats["removed"] += 1

        db.session.commit()

        # ── LOG HISTORY ──
        try:
            summary_str = f"Added: {stats['added']}, Updated: {stats['updated']}, Removed: {stats['removed']}, Unchanged: {stats['unchanged']}"
            new_history = UploadHistory(
                filename = filename,
                upload_date = upload_time,
                stats = summary_str,
                user = session.get("user", "System")
            )
            db.session.add(new_history)
            db.session.commit()
        except Exception as log_err:
            print(f"Failed to log history: {log_err}")

        # Move file to uploads folder instead of deleting
        os.makedirs("uploads", exist_ok=True)
        if 'new_history' in locals() and new_history.id:
            safe_filename = f"{new_history.id}_{filename}"
            final_path = os.path.join("uploads", safe_filename)
            import shutil
            shutil.move(temp_path, final_path)
        else:
            if os.path.exists(temp_path):
                os.remove(temp_path)


        msg = (
            f"Upload complete! "
            f" {stats['added']} new, "
            f" {stats['updated']} updated, "
            f" {stats['removed']} removed, "
            f" {stats['unchanged']} unchanged."
        )
        return jsonify({"message": msg, "stats": stats}), 200


    except Exception as e:

        import traceback
        traceback.print_exc()

        if os.path.exists(temp_path):
            os.remove(temp_path)

        return jsonify({"error": str(e)}), 500


@app.route("/download-history/<int:history_id>")
def download_history(history_id):
    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401
    
    from flask import send_file
    import os

    history = UploadHistory.query.get(history_id)
    if not history:
        return jsonify({"error": "Not found"}), 404
        
    safe_filename = f"{history.id}_{history.filename}"
    filepath = os.path.join("uploads", safe_filename)
    
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name=history.filename)
    else:
        return jsonify({"error": "File not found on server"}), 404


@app.route("/delete-history/<int:history_id>", methods=["DELETE"])
def delete_history(history_id):
    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401
    
    if session.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    history = UploadHistory.query.get(history_id)
    if not history:
        return jsonify({"error": "Not found"}), 404
        
    ts = history.upload_date # The timestamp used in DailyUpload.upload_timestamp
    
    # 1. REMOVE ASSOCIATED DATA from DailyUpload
    # We find all records that were part of this specific upload session
    DailyUpload.query.filter_by(upload_timestamp=ts).delete()
    
    # 2. DELETE FROM DB (History record)
    db.session.delete(history)
    db.session.commit()

    # 3. DELETE Physical file
    safe_filename = f"{history.id}_{history.filename}"
    filepath = os.path.join("uploads", safe_filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"Error removing file {filepath}: {e}")
            
    return jsonify({"message": "History and associated data deleted successfully"}), 200


@app.route("/clear-all-data", methods=["DELETE"])
def clear_all_data():
    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401
    
    if session.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403

    try:
        # Delete EVERY record from DailyUpload
        DailyUpload.query.delete()
        db.session.commit()
        return jsonify({"message": "All dashboard data cleared successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/uploaded-data")
def uploaded_data():
    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401

    role = session["role"]
    username = session["user"]

    query = DailyUpload.query
    if role != "admin":
        query = query.filter(DailyUpload.owner == username.lower())

    invoices = query.all()
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
        "comments": i.comments or "",
        "change_flag": i.change_flag or "unchanged",
        "is_active": i.is_active
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

    filename = f"daily_data_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
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