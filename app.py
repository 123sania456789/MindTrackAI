from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import jwt
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///mindtrack_ai.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import extensions
from extensions import db, migrate, login_manager, cors

# Initialize extensions with app
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
cors.init_app(app)

# Custom Jinja2 filters
@app.template_filter('from_json')
def from_json(value):
    if value:
        try:
            import json
            return json.loads(value)
        except:
            return []
    return []

# Import models first
from models import User, JournalEntry, MoodEntry, Task, Goal

# Import routes after models are initialized
from routes import auth_bp, journal_bp, mood_bp, tasks_bp, goals_bp, ml_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(journal_bp)
app.register_blueprint(mood_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(goals_bp)
app.register_blueprint(ml_bp)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


