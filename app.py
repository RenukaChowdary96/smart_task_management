from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task_management.db'
app.config['SECRET_KEY'] = 'supersecretkey'
db = SQLAlchemy(app)

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    role = db.Column(db.String(10), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default="Pending")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        email = request.form['email']
        role = request.form['role']
        
        new_user = User(username=username, password=password, email=email, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        flash('Invalid login credentials')
    return render_template('login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    users = User.query.filter_by(role='user').all()
    tasks = Task.query.all()
    return render_template('admin_dashboard.html', users=users, tasks=tasks)

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session or session['role'] != 'user':
        return redirect(url_for('login'))
    tasks = Task.query.filter_by(user_id=session['user_id']).all()
    return render_template('user_dashboard.html', tasks=tasks)

@app.route('/assign_task', methods=['POST'])
def assign_task():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    task_name = request.form['task_name']
    description = request.form['description']
    priority = request.form['priority']
    user_id = request.form['user_id']
    
    task = Task(name=task_name, description=description, priority=priority, user_id=user_id)
    db.session.add(task)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/update_task/<int:task_id>', methods=['POST'])
def update_task(task_id):
    if 'user_id' not in session or session['role'] != 'user':
        return redirect(url_for('login'))
    task = Task.query.get(task_id)
    if task.user_id == session['user_id']:
        task.status = request.form['status']
        db.session.commit()
    return redirect(url_for('user_dashboard'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure this is called within the app context
    app.run(debug=True)  # Start the Flask application
