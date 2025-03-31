from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from models import db, User, RepairRequest, Technician, Inventory, Payment

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------- Home Page --------
@app.route('/')
def index():
    return render_template('index.html')

# -------- User Registration --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        role = "customer"  # Default role

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists! Please log in.', 'danger')
            return redirect(url_for('login'))

        new_user = User(name=name, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# -------- User Login --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Try again.', 'danger')

    return render_template('login.html')

# -------- User Logout --------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

# -------- User Dashboard --------
@app.route('/dashboard')
@login_required
def dashboard():
    repair_requests = RepairRequest.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', requests=repair_requests)

# -------- Request a Repair --------
@app.route('/request_repair', methods=['GET', 'POST'])
@login_required
def request_repair():
    if request.method == 'POST':
        device = request.form['device']
        issue = request.form['issue']

        new_request = RepairRequest(user_id=current_user.id, device=device, issue=issue)
        db.session.add(new_request)
        db.session.commit()
        flash('Repair request submitted successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('request_form.html')

# -------- Track Repair Status --------
@app.route('/status/<int:request_id>')
@login_required
def track_status(request_id):
    repair_request = RepairRequest.query.get_or_404(request_id)
    return render_template('status.html', request=repair_request)

# -------- Admin Panel --------
@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('dashboard'))

    repair_requests = RepairRequest.query.all()
    return render_template('admin.html', requests=repair_requests)

# -------- Assign Technician --------
@app.route('/assign_technician/<int:request_id>', methods=['POST'])
@login_required
def assign_technician(request_id):
    if current_user.role != 'admin':
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('admin'))

    technician_id = request.form.get('technician_id')
    repair_request = RepairRequest.query.get_or_404(request_id)
    repair_request.assigned_technician = technician_id
    db.session.commit()
    flash('Technician assigned successfully!', 'success')
    return redirect(url_for('admin'))

# -------- Inventory Management --------
@app.route('/inventory')
@login_required
def inventory():
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('dashboard'))

    parts = Inventory.query.all()
    return render_template('inventory.html', parts=parts)

# -------- Payment Processing (Basic) --------
@app.route('/payment/<int:request_id>', methods=['POST'])
@login_required
def process_payment(request_id):
    amount = request.form['amount']
    new_payment = Payment(request_id=request_id, amount=amount, status="Paid")
    db.session.add(new_payment)
    db.session.commit()
    flash('Payment successful!', 'success')
    return redirect(url_for('dashboard'))

# -------- Run the App --------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
