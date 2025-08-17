from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, JournalEntry, MoodEntry, Task, Goal
from datetime import datetime
import jwt
from functools import wraps
import json

# Authentication Blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': 'User registered successfully'}), 201
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            return jsonify({'message': 'Login successful'}), 200
        
        return jsonify({'error': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Journal Blueprint
journal_bp = Blueprint('journal', __name__, url_prefix='/journal')

@journal_bp.route('/')
@login_required
def index():
    entries = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.created_at.desc()).all()
    return render_template('journal/index.html', entries=entries)

@journal_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_entry():
    if request.method == 'POST':
        data = request.get_json()
        entry = JournalEntry(
            user_id=current_user.id,
            title=data.get('title'),
            content=data.get('content'),
            mood_score=data.get('mood_score'),
            tags=json.dumps(data.get('tags', []))
        )
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({'message': 'Entry created successfully', 'id': entry.id}), 201
    
    return render_template('journal/new.html')

@journal_bp.route('/<int:entry_id>')
@login_required
def view_entry(entry_id):
    entry = JournalEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    return render_template('journal/view.html', entry=entry)

# Mood Tracking Blueprint
mood_bp = Blueprint('mood', __name__, url_prefix='/mood')

@mood_bp.route('/')
@login_required
def index():
    entries = MoodEntry.query.filter_by(user_id=current_user.id).order_by(MoodEntry.created_at.desc()).limit(30).all()
    return render_template('mood/index.html', entries=entries)

@mood_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_entry():
    if request.method == 'POST':
        data = request.get_json()
        entry = MoodEntry(
            user_id=current_user.id,
            mood_score=data.get('mood_score'),
            mood_label=data.get('mood_label'),
            notes=data.get('notes'),
            activities=json.dumps(data.get('activities', [])),
            sleep_hours=data.get('sleep_hours'),
            exercise_minutes=data.get('exercise_minutes'),
            social_interactions=data.get('social_interactions')
        )
        db.session.add(entry)
        db.session.commit()
        return jsonify({'message': 'Mood entry created successfully'}), 201
    
    return render_template('mood/new.html')

# Tasks Blueprint
tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')

@tasks_bp.route('/')
@login_required
def index():
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.due_date.asc()).all()
    return render_template('tasks/index.html', tasks=tasks)

@tasks_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_task():
    if request.method == 'POST':
        data = request.get_json()
        task = Task(
            user_id=current_user.id,
            title=data.get('title'),
            description=data.get('description'),
            priority=data.get('priority', 'medium'),
            due_date=datetime.fromisoformat(data.get('due_date')) if data.get('due_date') else None
        )
        db.session.add(task)
        db.session.commit()
        return jsonify({'message': 'Task created successfully'}), 201
    
    return render_template('tasks/new.html')

@tasks_bp.route('/<int:task_id>/complete')
@login_required
def complete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    task.status = 'completed'
    task.completed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Task completed'}), 200

# Goals Blueprint
goals_bp = Blueprint('goals', __name__, url_prefix='/goals')

@goals_bp.route('/')
@login_required
def index():
    goals = Goal.query.filter_by(user_id=current_user.id).order_by(Goal.target_date.asc()).all()
    return render_template('goals/index.html', goals=goals)

@goals_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_goal():
    if request.method == 'POST':
        data = request.get_json()
        goal = Goal(
            user_id=current_user.id,
            title=data.get('title'),
            description=data.get('description'),
            category=data.get('category'),
            target_date=datetime.fromisoformat(data.get('target_date')).date() if data.get('target_date') else None
        )
        db.session.add(goal)
        db.session.commit()
        return jsonify({'message': 'Goal created successfully'}), 201
    
    return render_template('goals/new.html')

@goals_bp.route('/<int:goal_id>/update_progress', methods=['POST'])
@login_required
def update_progress(goal_id):
    data = request.get_json()
    goal = Goal.query.filter_by(id=goal_id, user_id=current_user.id).first_or_404()
    goal.progress = data.get('progress', 0)
    db.session.commit()
    return jsonify({'message': 'Progress updated successfully'}), 200

# ML Services Blueprint
ml_bp = Blueprint('ml', __name__, url_prefix='/ml')

@ml_bp.route('/insights')
@login_required
def insights():
    # Get user's data for insights
    journal_entries = JournalEntry.query.filter_by(user_id=current_user.id).all()
    mood_entries = MoodEntry.query.filter_by(user_id=current_user.id).all()
    
    # Calculate basic statistics
    total_entries = len(journal_entries)
    avg_mood = sum(entry.mood_score for entry in mood_entries) / len(mood_entries) if mood_entries else 0
    
    return render_template('ml/insights.html', 
                         total_entries=total_entries,
                         avg_mood=avg_mood,
                         journal_entries=journal_entries,
                         mood_entries=mood_entries)

@ml_bp.route('/sentiment_analysis', methods=['POST'])
@login_required
def sentiment_analysis():
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    # Simple sentiment analysis (placeholder for ML service)
    result = {
        'sentiment': 'neutral',
        'confidence': 0.5,
        'text': text
    }
    
    return jsonify(result)

# Doctor Recommendations Blueprint
doctors_bp = Blueprint('doctors', __name__, url_prefix='/doctors')

@doctors_bp.route('/')
@login_required
def index():
    """Show doctor recommendations page"""
    return render_template('doctors/index.html')

@doctors_bp.route('/search')
@login_required
def search_doctors():
    """Search for doctors based on criteria"""
    specialty = request.args.get('specialty', '')
    location = request.args.get('location', '')
    
    # Mock doctor data - in production, this would integrate with real APIs
    mock_doctors = [
        {
            'id': 1,
            'name': 'Dr. Sarah Johnson',
            'specialty': 'Psychiatrist',
            'subspecialty': 'Depression & Anxiety',
            'distance': '0.5 miles',
            'rating': 4.8,
            'review_count': 127,
            'address': '123 Main St, City, State 12345',
            'phone': '(555) 123-4567',
            'email': 'dr.johnson@example.com',
            'available': True,
            'next_available': 'Tomorrow 2:00 PM',
            'accepts_insurance': True,
            'languages': ['English', 'Spanish'],
            'years_experience': 15,
            'education': 'Harvard Medical School',
            'certifications': ['Board Certified Psychiatrist', 'Fellow of American Psychiatric Association']
        },
        {
            'id': 2,
            'name': 'Dr. Michael Chen',
            'specialty': 'Psychologist',
            'subspecialty': 'Cognitive Behavioral Therapy',
            'distance': '1.2 miles',
            'rating': 4.6,
            'review_count': 89,
            'address': '456 Oak Ave, City, State 12345',
            'phone': '(555) 234-5678',
            'email': 'dr.chen@example.com',
            'available': True,
            'next_available': 'Today 4:00 PM',
            'accepts_insurance': True,
            'languages': ['English', 'Mandarin'],
            'years_experience': 12,
            'education': 'Stanford University',
            'certifications': ['Licensed Clinical Psychologist', 'CBT Specialist']
        },
        {
            'id': 3,
            'name': 'Dr. Emily Rodriguez',
            'specialty': 'Therapist',
            'subspecialty': 'Trauma & PTSD',
            'distance': '2.1 miles',
            'rating': 4.9,
            'review_count': 203,
            'address': '789 Pine Rd, City, State 12345',
            'phone': '(555) 345-6789',
            'email': 'dr.rodriguez@example.com',
            'available': False,
            'next_available': 'Next Week',
            'accepts_insurance': False,
            'languages': ['English', 'Spanish'],
            'years_experience': 8,
            'education': 'UCLA',
            'certifications': ['Licensed Marriage and Family Therapist', 'EMDR Certified']
        },
        {
            'id': 4,
            'name': 'Dr. James Wilson',
            'specialty': 'Psychiatrist',
            'subspecialty': 'Bipolar Disorder',
            'distance': '3.2 miles',
            'rating': 4.7,
            'review_count': 156,
            'address': '321 Elm St, City, State 12345',
            'phone': '(555) 456-7890',
            'email': 'dr.wilson@example.com',
            'available': True,
            'next_available': 'Today 6:00 PM',
            'accepts_insurance': True,
            'languages': ['English'],
            'years_experience': 20,
            'education': 'Johns Hopkins University',
            'certifications': ['Board Certified Psychiatrist', 'Mood Disorders Specialist']
        }
    ]
    
    # Filter by specialty if provided
    if specialty:
        mock_doctors = [d for d in mock_doctors if specialty.lower() in d['specialty'].lower()]
    
    return jsonify(mock_doctors)

@doctors_bp.route('/<int:doctor_id>')
@login_required
def doctor_detail(doctor_id):
    """Show detailed information about a specific doctor"""
    # In production, this would fetch from a database or API
    return render_template('doctors/detail.html', doctor_id=doctor_id)

@doctors_bp.route('/appointment', methods=['POST'])
@login_required
def book_appointment():
    """Book an appointment with a doctor"""
    data = request.get_json()
    doctor_id = data.get('doctor_id')
    appointment_date = data.get('appointment_date')
    appointment_time = data.get('appointment_time')
    reason = data.get('reason')
    
    # In production, this would create an appointment record
    # For now, just return success
    return jsonify({
        'message': 'Appointment request submitted successfully',
        'appointment_id': 12345,
        'status': 'pending_confirmation'
    }), 201


