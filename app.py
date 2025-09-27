import sqlite3
from flask import Flask, render_template, request, redirect, session, g, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'complaints.db')

app = Flask(__name__)
app.jinja_env.globals['datetime'] = datetime
app.secret_key = 'replace-with-a-secure-random-key'  # change before production

# ---------- DB helper ----------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# ---------- Auth helpers ----------
def get_user_by_email(email):
    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE email = ?', (email,))
    return cur.fetchone()

def get_user_by_id(uid):
    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE id = ?', (uid,))
    return cur.fetchone()

# ---------- Routes ----------
@app.route('/')
def index():
    return render_template('index.html', datetime=datetime)

# Register (citizen)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        region = request.form.get('region')

        if not name or not email or not password:
            flash('Please fill all required fields.', 'danger')
            return redirect(url_for('register'))

        if get_user_by_email(email):
            flash('Email is already registered.', 'danger')
            return redirect(url_for('register'))

        hashed = generate_password_hash(password)
        db = get_db()
        db.execute('INSERT INTO users (name, email, password, role, region) VALUES (?, ?, ?, ?, ?)',
                   (name, email, hashed, 'citizen', region))
        db.commit()
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', datetime=datetime)

# Login (both)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        user = get_user_by_email(email)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']
            flash('Logged in successfully.', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('citizen_dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html', datetime=datetime)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('index'))

# Complaint form (citizen)
@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if 'user_id' not in session:
        flash('You must be logged in to submit a complaint.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        department = request.form.get('department')
        region = request.form.get('region')
        description = request.form.get('description').strip()
        if not department or not region or not description:
            flash('All fields are required.', 'danger')
            return redirect(url_for('complaint'))

        db = get_db()
        db.execute('INSERT INTO complaints (user_id, department, region, description, status, date_submitted) VALUES (?, ?, ?, ?, ?, ?)',
                   (session['user_id'], department, region, description, 'Pending', datetime.utcnow().isoformat()))
        db.commit()
        return render_template('success.html', message="Your complaint has been submitted.")

    departments = ["Municipality", "Electricity", "Corruption", "Police Grievance", "Harassment", "Roads", "Water Supply", "Other"]
    regions = ["North", "South", "East", "West", "Central", "Head Office"]  # adjust as needed
    return render_template('complaint_form.html', departments=departments, regions=regions, datetime=datetime)

# Citizen dashboard
@app.route('/citizen/dashboard')
def citizen_dashboard():
    if 'user_id' not in session or session.get('role') != 'citizen':
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))

    db = get_db()
    cur = db.execute('SELECT * FROM complaints WHERE user_id = ? ORDER BY date_submitted DESC', (session['user_id'],))
    complaints = cur.fetchall()
    return render_template('citizen_dashboard.html', complaints=complaints, datetime=datetime)

# Admin dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('login'))

    # optional filters
    dept = request.args.get('department')
    region = request.args.get('region')
    db = get_db()
    query = 'SELECT c.*, u.name as submitter_name, u.email as submitter_email FROM complaints c LEFT JOIN users u ON c.user_id = u.id'
    params = ()
    conditions = []
    if dept:
        conditions.append('c.department = ?')
        params += (dept,)
    if region:
        conditions.append('c.region = ?')
        params += (region,)
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    query += ' ORDER BY c.date_submitted DESC'
    cur = db.execute(query, params)
    complaints = cur.fetchall()
    departments = ["Municipality", "Electricity", "Corruption", "Police Grievance", "Harassment", "Roads", "Water Supply", "Other"]
    regions = ["North", "South", "East", "West", "Central", "Head Office"]
    return render_template('admin_dashboard.html', complaints=complaints, departments=departments, regions=regions, datetime=datetime)

# Update status (admin)
@app.route('/update_status/<int:cid>', methods=['POST'])
def update_status(cid):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('login'))
    new_status = request.form.get('status')
    db = get_db()
    db.execute('UPDATE complaints SET status = ? WHERE id = ?', (new_status, cid))
    db.commit()
    flash('Status updated.', 'success')
    return redirect(url_for('admin_dashboard'))

# About
@app.route('/about')
def about():
    return render_template('about.html', datetime=datetime)

# Settings
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        flash('Login required.', 'warning')
        return redirect(url_for('login'))
    db = get_db()
    user = get_user_by_id(session['user_id'])
    if request.method == 'POST':
        region = request.form.get('region')
        db.execute('UPDATE users SET region = ? WHERE id = ?', (region, session['user_id']))
        db.commit()
        flash('Settings updated.', 'success')
        return redirect(url_for('settings'))
    regions = ["North", "South", "East", "West", "Central", "Head Office"]
    return render_template('settings.html', user=user, regions=regions, datetime=datetime)

if __name__ == '__main__':
    # ensure DB exists
    if not os.path.exists(DB_PATH):
        print("Database not found. Run create_db.py to create DB with admin user.")
    app.run(debug=True)
