from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    role = db.Column(db.String(20))  


class Invoice(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    transaction_no = db.Column(db.String(50))
    customer = db.Column(db.String(200))

    amount = db.Column(db.Float)
    balance_due = db.Column(db.Float)

    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))

    ageing = db.Column(db.Integer)

    owner = db.Column(db.String(100))
    status = db.Column(db.String(50))


class DailyUpload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ageing = db.Column(db.String(50))
    date = db.Column(db.String(20))
    transaction_no = db.Column(db.String(50))
    type = db.Column(db.String(50))
    status = db.Column(db.String(50))
    customer_name = db.Column(db.String(200))
    age = db.Column(db.Float)
    amount = db.Column(db.Float)
    balance_due = db.Column(db.Float)
    owner = db.Column(db.String(100))
    domain_name = db.Column(db.String(200))
    payment_received_date = db.Column(db.String(20))
    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))
    upload_timestamp = db.Column(db.String(50))
    custom_status = db.Column(db.String(50), default="Pending")
    comments = db.Column(db.Text, default="")
    change_flag = db.Column(db.String(20), default="unchanged")
    is_active = db.Column(db.Boolean, default=True)
    serial_no = db.Column(db.Integer, default=0)   # 1-based row number within the upload batch



class UploadHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    upload_date = db.Column(db.String(50))
    stats = db.Column(db.Text)  # JSON-like string: "added: 1, updated: 2..."
    user = db.Column(db.String(100))


class Task(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    assigned_to = db.Column(db.String(100))   # owner/agent username
    created_by  = db.Column(db.String(100))   # admin username
    categories  = db.Column(db.String(200))   # CSV: "overdue,before"
    created_at  = db.Column(db.String(50))
    invoices    = db.relationship('TaskInvoice', backref='task', lazy=True,
                                  cascade='all, delete-orphan')


class TaskInvoice(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    task_id       = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    daily_id      = db.Column(db.Integer)          # DailyUpload.id (snapshot reference)
    invoice_no    = db.Column(db.String(100))
    customer_name = db.Column(db.String(200))
    serial_no     = db.Column(db.Integer)
    balance_due   = db.Column(db.Float)
    category      = db.Column(db.String(50))       # which category bucket
    follow_up     = db.Column(db.Text, default="")
    remark_status = db.Column(db.String(50), default="Pending")  # Pending/Called/Resolved/Escalate
    updated_at    = db.Column(db.String(50), default="")

