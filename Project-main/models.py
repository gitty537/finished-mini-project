from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Users Table (For Customers and Admins)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="customer")  # "customer" or "admin"
    repair_requests = db.relationship('RepairRequest', backref='customer', lazy=True)

# Repair Requests Table
class RepairRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    device = db.Column(db.String(100), nullable=False)
    issue = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default="Pending")
    assigned_technician = db.Column(db.Integer, db.ForeignKey('technician.id'), nullable=True)
    payments = db.relationship('Payment', backref='repair_request', lazy=True)

# Technicians Table
class Technician(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    repair_requests = db.relationship('RepairRequest', backref='technician', lazy=True)

# Inventory Table (For Spare Parts Tracking)
class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    part_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, nullable=False)

# Payments Table
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('repair_request.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="Pending")  # "Paid" or "Pending"
