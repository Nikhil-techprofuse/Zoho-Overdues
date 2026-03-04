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