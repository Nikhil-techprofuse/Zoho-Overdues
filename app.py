from flask import Flask, render_template, request, jsonify, session
from models import db, User, Invoice

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
    return render_template("index.html")


@app.route("/dashboard")
def dashboard_page():
    if not require_login():
        return render_template("index.html")
    return render_template("dashboard.html")


@app.route("/invoices-page")
def invoices_page():
    if not require_login():
        return render_template("index.html")
    return render_template("invoices.html")


@app.route("/customers-page")
def customers_page():
    if not require_login():
        return render_template("index.html")
    return render_template("customers.html")


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

    query = Invoice.query

    # Owner restriction
    if role != "admin":
        query = query.filter_by(owner=username)

    invoices = query.all()

    total_value = sum(i.amount or 0 for i in invoices)
    total_due = sum(i.balance_due or 0 for i in invoices)
    total_invoices = len(invoices)
    unique_customers = len(set(i.customer for i in invoices if i.customer))

    return jsonify({
        "totalValue": total_value,
        "totalDue": total_due,
        "totalInvoices": total_invoices,
        "uniqueCustomers": unique_customers
    })


# =====================================================
# INVOICES API
# =====================================================

@app.route("/invoices")
def invoices():

    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401

    role = session["role"]
    username = session["user"]

    query = Invoice.query

    if role != "admin":
        query = query.filter_by(owner=username)

    invoices = query.all()

    result = [{
        "invoice": i.transaction_no,
        "customer": i.customer,
        "amount": i.amount,
        "due": i.balance_due,
        "start": i.start_date,
        "end": i.end_date,
        "ageing": i.ageing,
        "owner": i.owner,
        "status": i.status
    } for i in invoices]

    return jsonify(result)


# =====================================================
# UNIQUE CUSTOMERS API
# =====================================================

@app.route("/customers-data")
def customers_data():

    if not require_login():
        return jsonify({"error": "Unauthorized"}), 401

    role = session["role"]
    username = session["user"]

    query = Invoice.query

    if role != "admin":
        query = query.filter_by(owner=username)

    invoices = query.all()

    customers = {}

    for i in invoices:

        if not i.customer:
            continue

        if i.customer not in customers:
            customers[i.customer] = {
                "customer": i.customer,
                "total_due": 0,
                "invoices": []
            }

        customers[i.customer]["total_due"] += i.balance_due or 0

        customers[i.customer]["invoices"].append({
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
    return render_template("agent.html")

@app.route("/agent-data")
def agent_data():

    if not require_login():
        return jsonify({"error":"Unauthorized"}),401

    role = session["role"]
    username = session["user"]

    query = Invoice.query

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
            "customer": i.customer,
            "due": i.balance_due
        })

    return jsonify(list(agents.values()))

# =====================================================
# RUN APP
# =====================================================

if __name__ == "__main__":
    app.run(debug=True)