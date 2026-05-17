from collections import deque
import os
import secrets
import sys

MOD = 10**9 + 7
NEG_INF = -10**60
HASH_PREFIXES = ("pbkdf2:", "scrypt:")


def max_net_profit(values, k, switch_cost):
    n = len(values)

    if n == 0:
        return 0

    prefix = [0] * (n + 1)
    for index, value in enumerate(values, start=1):
        prefix[index] = prefix[index - 1] + value

    collect = [NEG_INF] * (n + 1)
    skip = [NEG_INF] * (n + 1)
    candidates = deque()

    for index in range(1, n + 1):
        while candidates and candidates[0][0] < index - k:
            candidates.popleft()

        best_collect = prefix[index] if index <= k else NEG_INF
        if candidates:
            best_collect = max(best_collect, prefix[index] + candidates[0][1])
        collect[index] = best_collect

        if index > 1:
            skip[index] = max(skip[index - 1], collect[index - 1] - switch_cost)

        candidate_value = skip[index] - switch_cost - prefix[index]
        if candidate_value > NEG_INF // 2:
            while candidates and candidates[-1][1] <= candidate_value:
                candidates.pop()
            candidates.append((index, candidate_value))

    return max(collect[n], skip[n])


def solve(data=None):
    tokens = data.split() if data is not None else sys.stdin.buffer.read().split()

    if not tokens:
        return ""

    n = int(tokens[0])
    k = int(tokens[1])
    switch_cost = int(tokens[2])
    values = list(map(int, tokens[3:3 + n]))

    if len(values) != n:
        raise ValueError("Input array length does not match n")

    return str(max_net_profit(values, k, switch_cost) % MOD)


def is_password_hash(value):
    return isinstance(value, str) and value.startswith(HASH_PREFIXES)


def load_secret_key():
    configured_key = os.environ.get("SECRET_KEY")
    if configured_key:
        return configured_key

    key_path = os.path.join(os.path.dirname(__file__), ".flask_secret_key")
    if os.path.exists(key_path):
        with open(key_path, "r", encoding="utf-8") as key_file:
            stored_key = key_file.read().strip()
        if stored_key:
            return stored_key

    generated_key = secrets.token_hex(32)
    with open(key_path, "w", encoding="utf-8") as key_file:
        key_file.write(generated_key)
    return generated_key


def env_flag(name):
    return os.environ.get(name, "0").strip().lower() in {"1", "true", "yes", "on"}


try:
    from flask import Flask, jsonify, render_template, request, session
    from models import Invoice, User, db
    from werkzeug.security import check_password_hash, generate_password_hash
except ModuleNotFoundError:
    Flask = None
    app = None
else:
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = load_secret_key()

    db.init_app(app)

    with app.app_context():
        db.create_all()

        updated_users = False
        for user in User.query.all():
            if not is_password_hash(user.password):
                user.password = generate_password_hash(user.password)
                updated_users = True

        if updated_users:
            db.session.commit()

        if not User.query.first():
            users = [
                User(username="admin", password=generate_password_hash("admin123"), role="admin"),
                User(username="srilakshmi", password=generate_password_hash("owner123"), role="owner"),
                User(username="sireesha", password=generate_password_hash("owner123"), role="owner"),
                User(username="vamsi", password=generate_password_hash("owner123"), role="owner"),
                User(username="vijay", password=generate_password_hash("owner123"), role="owner"),
                User(username="shravya", password=generate_password_hash("owner123"), role="owner"),
            ]

            db.session.add_all(users)
            db.session.commit()

    def require_login():
        return "user" in session and "role" in session


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


    @app.route("/login", methods=["POST"])
    def login():
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")

        user = User.query.filter_by(username=username).first()

        if not user or not (
            is_password_hash(user.password) and check_password_hash(user.password, password)
        ):
            return jsonify({"message": "Invalid credentials"}), 401

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


    @app.route("/dashboard-data")
    def dashboard_data():
        if not require_login():
            return jsonify({"error": "Unauthorized"}), 401

        role = session["role"]
        username = session["user"]

        query = Invoice.query

        if role != "admin":
            query = query.filter_by(owner=username)

        invoices = query.all()

        total_value = sum(invoice.amount or 0 for invoice in invoices)
        total_due = sum(invoice.balance_due or 0 for invoice in invoices)
        total_invoices = len(invoices)
        unique_customers = len(set(invoice.customer for invoice in invoices if invoice.customer))

        return jsonify({
            "totalValue": total_value,
            "totalDue": total_due,
            "totalInvoices": total_invoices,
            "uniqueCustomers": unique_customers
        })


    @app.route("/invoices")
    def invoices():
        if not require_login():
            return jsonify({"error": "Unauthorized"}), 401

        role = session["role"]
        username = session["user"]

        query = Invoice.query

        if role != "admin":
            query = query.filter_by(owner=username)

        all_invoices = query.all()

        result = [{
            "invoice": invoice.transaction_no,
            "customer": invoice.customer,
            "amount": invoice.amount,
            "due": invoice.balance_due,
            "start": invoice.start_date,
            "end": invoice.end_date,
            "ageing": invoice.ageing,
            "owner": invoice.owner,
            "status": invoice.status
        } for invoice in all_invoices]

        return jsonify(result)


    @app.route("/customers-data")
    def customers_data():
        if not require_login():
            return jsonify({"error": "Unauthorized"}), 401

        role = session["role"]
        username = session["user"]

        query = Invoice.query

        if role != "admin":
            query = query.filter_by(owner=username)

        all_invoices = query.all()
        customers = {}

        for invoice in all_invoices:
            if not invoice.customer:
                continue

            if invoice.customer not in customers:
                customers[invoice.customer] = {
                    "customer": invoice.customer,
                    "total_due": 0,
                    "invoices": []
                }

            customers[invoice.customer]["total_due"] += invoice.balance_due or 0
            customers[invoice.customer]["invoices"].append({
                "invoice": invoice.transaction_no,
                "amount": invoice.amount,
                "due": invoice.balance_due,
                "status": invoice.status,
                "owner": invoice.owner
            })

        return jsonify(list(customers.values()))


    @app.route("/agent-page")
    def agent_page():
        if not require_login():
            return render_template("index.html")
        return render_template("agent.html")


    @app.route("/agent-data")
    def agent_data():
        if not require_login():
            return jsonify({"error": "Unauthorized"}), 401

        role = session["role"]
        username = session["user"]

        query = Invoice.query

        if role != "admin":
            query = query.filter_by(owner=username)

        all_invoices = query.all()
        agents = {}

        for invoice in all_invoices:
            if not invoice.owner:
                continue

            if invoice.owner not in agents:
                agents[invoice.owner] = {
                    "owner": invoice.owner,
                    "total_amount": 0,
                    "total_due": 0,
                    "invoice_count": 0,
                    "invoices": []
                }

            agents[invoice.owner]["total_amount"] += invoice.amount or 0
            agents[invoice.owner]["total_due"] += invoice.balance_due or 0
            agents[invoice.owner]["invoice_count"] += 1
            agents[invoice.owner]["invoices"].append({
                "invoice": invoice.transaction_no,
                "customer": invoice.customer,
                "due": invoice.balance_due
            })

        return jsonify(list(agents.values()))


def run_flask_app():
    if app is None:
        raise RuntimeError("Flask dependencies are not available")
    app.run(debug=env_flag("FLASK_DEBUG"))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        run_flask_app()
    else:
        result = solve()
        if result:
            sys.stdout.write(result)
