from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from models import db, User, RepairRequest, Technician, Inventory, Payment

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root123@localhost/electronic'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) if user_id else None

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
        password = request.form['password']
        role = request.form.get('role', 'customer')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists! Please log in.', 'danger')
            return redirect(url_for('login'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(name=name, email=email, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# -------- User Login --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

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

        # Debugging statement
        print(f"New Repair Request ID: {new_request.id}")

        if not new_request.id:
            flash('Error: Request ID not generated.', 'danger')
            return redirect(url_for('dashboard'))

        flash('Repair request submitted successfully!', 'success')
        return redirect(url_for('process_payment', request_id=new_request.id))  # Ensure this ID exists

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
        return redirect(url_for('dashboard'))

    repair_requests = RepairRequest.query.all()
    technicians = Technician.query.all()
    return render_template('admin.html', requests=repair_requests, technicians=technicians)

# -------- Assign Technician --------
@app.route('/assign_technician/<int:request_id>', methods=['POST'])
@login_required
def assign_technician(request_id):
    if current_user.role != 'admin':
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('dashboard'))

    technician_id = request.form.get('technician_id')
    repair_request = RepairRequest.query.get_or_404(request_id)
    
    if technician_id and technician_id.isdigit():
        repair_request.assigned_technician = int(technician_id)
        db.session.commit()
        flash('Technician assigned successfully!', 'success')
        return redirect(url_for('process_payment', request_id=request_id))
    else:
        flash('Invalid technician ID!', 'danger')
    
    return redirect(url_for('admin'))

# -------- Inventory Management --------

@app.route('/inv', methods=['GET', 'POST'])
@login_required
def inventory():
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        part_name = request.form.get('part_name')
        quantity = request.form.get('quantity')
        price = request.form.get('price')  # Capture price

        if not part_name or not quantity or not price:
            flash('All fields are required!', 'danger')
        else:
            new_part = Inventory(part_name=part_name, quantity=int(quantity), price=float(price))
            db.session.add(new_part)
            db.session.commit()
            flash('Item added to inventory successfully!', 'success')

    parts = Inventory.query.all()
    return render_template('inventory.html', parts=parts)

#---------deleting inventory-----------
@app.route('/delete_inv/<int:part_id>', methods=['POST'])
@login_required
def delete_inventory(part_id):
    if current_user.role != 'admin':
        flash('Unauthorized action!', 'danger')
        return redirect(url_for('inventory'))   

    part = Inventory.query.get_or_404(part_id)
    db.session.delete(part)
    db.session.commit()
    flash(f'Item "{part.part_name}" deleted successfully!', 'success')
    
    return redirect(url_for('inventory'))


# -------- Payment Processing --------
@app.route('/payment/<int:request_id>', methods=['GET', 'POST'])
@login_required
def process_payment(request_id):
    repair_request = RepairRequest.query.get_or_404(request_id)

    if request.method == 'POST':
        amount = request.form.get('amount')
        
        if not amount or not amount.isdigit():
            flash('Invalid amount!', 'danger')
            return redirect(url_for('process_payment', request_id=request_id))

        new_payment = Payment(request_id=request_id, amount=int(amount), status="Paid")
        db.session.add(new_payment)
        db.session.commit()
        flash('Payment successful!', 'success')

        return redirect(url_for('dashboard'))

    return render_template('payment.html', request=repair_request)


# -------- Run the App --------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
