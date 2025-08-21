from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User, JournalEntry, MoodEntry, Task, Goal, AssessmentSession, ChatMessage
from datetime import datetime
import jwt
from functools import wraps
import json
import random
from typing import Dict, Any, List

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
            'name': 'Dr. Kapur B, MD',
            'specialty': 'Psychiatrist',
            'subspecialty': 'Depression & Schizophrenia',
            'distance': 'Hebbal',
            'rating': 4.8,
            'review_count': 127,
            'address': 'Hebbal, Manipal Hospital, Bangalore, Karnataka 560036',
            'phone': '8046808476',
            'email': 'NA',
            'available': True,
            'next_available': 'Visit Website',
            'accepts_insurance': True,
            'languages': ['English', 'Hindi', 'Punjabi'],
            'years_experience': 47,
            'education': 'AFMC, PUNE',
            'certifications': ['Board Certified in Psychiatry', 'Fellow of American Psychiatric Association']
        },
        {
            'id': 2,
            'name': 'Dr. Krishen Ranganath',
            'specialty': 'Psychiatrist',
            'subspecialty': 'Autism, Dyslexia, Eating Disorders, Mood Disorders, PTSD',
            'distance': 'Seshadripuram / Basaveshwara Nagar',
            'rating': 4.9,
            'review_count': 167,
            'address': 'Apollo Hospitals Sheshadripuram & BINDIG MINDCARE, Bangalore',
            'phone': '+91 80 4668 8888',
            'email': 'NA',
            'available': True,
            'next_available': 'Book via Practo / Clinic inquiry',
            'accepts_insurance': False,
            'languages': ['English', 'Hindi', 'Kannada', 'Tamil', 'Telugu'],
            'years_experience': 18,
            'education': 'MBBS, MRCPsych (UK), Diploma in Clinical Psychiatry (Ireland), PG Dip Clinical Neuropsychiatry (Birmingham, UK)',
            'certifications': [
                'Medical Registration Verified',
                'Certificate (Part 1) in Clinical Psychopharmacology – BAP',
                'Internship in Medical Leadership (UK)'
            ]
        },
        {
            'id': 3,
            'name': 'Dr. Bhupendra Chaudhry',
            'specialty': 'Psychiatrist',
            'subspecialty': 'Depression, Anxiety Disorders, OCD, Schizophrenia, Addiction, Psychiatric Emergencies, Child & Adolescent Issues',
            'distance': 'Koramangala / Old Airport Road / Kumara Park West',
            'rating': 4.6,
            'review_count': 124,
            'address': 'Apollo Medical Centre; Manipal Hospital — Old Airport Road; Mallige Medical Centre, Bangalore',
            'phone': '18001024647',
            'email': 'NA',
            'available': True,
            'next_available': 'Book via Practo or Apollo platform',
            'accepts_insurance': False,
            'languages': ['English', 'Hindi', 'Kannada'],
            'years_experience': 33,
            'education': 'MBBS (Kanpur University), MD Psychiatry (SNMC, Agra)',
            'certifications': [
                'Karnataka Medical Council Reg 79231',
                'Member of Indian Psychiatric Society'
            ]
        },
        {
            'id': 4,
            'name': 'Dr. Chandra Shekar M',
            'specialty': 'Psychiatrist',
            'subspecialty': 'General Psychiatry, Child Psychiatry, De-addiction',
            'distance': 'RT Nagar / Horamavu',
            'rating': 4.5,
            'review_count': 18,
            'address': 'Medax Hospitals (RT Nagar); Trust-In Hospital (Horamavu); Sridi Sai Hospital — various clinics in Bangalore',
            'phone': 'On-call via Practo/clinic inquiry',
            'email': 'NA',
            'available': True,
            'next_available': 'Book via Practo or hospital portal',
            'accepts_insurance': False,
            'languages': ['English', 'Hindi'],
            'years_experience': 31,
            'education': 'MBBS; DPM Psychiatry (NIMHANS); DNB Psychiatry (NIMHANS)',
            'certifications': [
                'Karnataka Medical Council Reg 39712',
                'Indian Psychiatric Society',
                'Karnataka Psychiatric Society'
            ]
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


# Assessments Blueprint (PHQ-9 + SCID-5-PD screening with branching)
assessments_bp = Blueprint('assessments', __name__, url_prefix='/assessments')


def _phq9_bank() -> List[Dict[str, Any]]:
    # Minimal PHQ-9 item bank
    items = [
        {'id': 'phq1', 'text': 'Little interest or pleasure in doing things', 'type': 'likert', 'options': [0, 1, 2, 3]},
        {'id': 'phq2', 'text': 'Feeling down, depressed, or hopeless', 'type': 'likert', 'options': [0, 1, 2, 3]},
        {'id': 'phq3', 'text': 'Trouble falling or staying asleep, or sleeping too much', 'type': 'likert', 'options': [0, 1, 2, 3]},
        {'id': 'phq4', 'text': 'Feeling tired or having little energy', 'type': 'likert', 'options': [0, 1, 2, 3]},
        {'id': 'phq5', 'text': 'Poor appetite or overeating', 'type': 'likert', 'options': [0, 1, 2, 3]},
        {'id': 'phq6', 'text': 'Feeling bad about yourself — or that you are a failure or have let yourself or your family down', 'type': 'likert', 'options': [0, 1, 2, 3]},
        {'id': 'phq7', 'text': 'Trouble concentrating on things, such as reading or watching television', 'type': 'likert', 'options': [0, 1, 2, 3]},
        {'id': 'phq8', 'text': 'Moving or speaking so slowly that other people could have noticed, or being so fidgety or restless that you have been moving a lot more than usual', 'type': 'likert', 'options': [0, 1, 2, 3]},
        {'id': 'phq9', 'text': 'Thoughts that you would be better off dead or of hurting yourself', 'type': 'likert', 'options': [0, 1, 2, 3]},
    ]
    return items


def _scid5pd_bank() -> List[Dict[str, Any]]:
    # Screening subset (~24 items) yes/no style, covering multiple domains; not the full copyrighted text
    items = [
        {'id': 'scid1', 'text': 'Do you often feel a pervasive pattern of distrust and suspicion of others?', 'type': 'bool'},
        {'id': 'scid2', 'text': 'Do you prefer being alone and have little interest in close relationships?', 'type': 'bool'},
        {'id': 'scid3', 'text': 'Do you believe you have special powers or unusual perceptual experiences?', 'type': 'bool'},
        {'id': 'scid4', 'text': 'Do you avoid social situations because of fears of criticism or rejection?', 'type': 'bool'},
        {'id': 'scid5', 'text': 'Do you need to be the center of attention and feel uncomfortable when you are not?', 'type': 'bool'},
        {'id': 'scid6', 'text': 'Do you lack empathy and often exploit others for your own benefit?', 'type': 'bool'},
        {'id': 'scid7', 'text': 'Do you act impulsively and have difficulty planning ahead?', 'type': 'bool'},
        {'id': 'scid8', 'text': 'Do you experience unstable and intense relationships with rapid mood changes?', 'type': 'bool'},
        {'id': 'scid9', 'text': 'Do you have a pervasive pattern of detachment and limited emotional expression?', 'type': 'bool'},
        {'id': 'scid10', 'text': 'Are you excessively devoted to work and productivity to the exclusion of leisure and friendships?', 'type': 'bool'},
        {'id': 'scid11', 'text': 'Are you preoccupied with orderliness, perfectionism, and control?', 'type': 'bool'},
        {'id': 'scid12', 'text': 'Do you fear being alone and go to great lengths to obtain nurturance and support from others?', 'type': 'bool'},
        {'id': 'scid13', 'text': 'Do you have an inflated sense of self-importance and need for admiration?', 'type': 'bool'},
        {'id': 'scid14', 'text': 'Do you frequently disregard social norms or the rights of others?', 'type': 'bool'},
        {'id': 'scid15', 'text': 'Do you feel uncomfortable unless others take responsibility for most areas of your life?', 'type': 'bool'},
        {'id': 'scid16', 'text': 'Do you often have odd beliefs or magical thinking that influences behavior?', 'type': 'bool'},
        {'id': 'scid17', 'text': 'Do you often hold grudges and perceive benign remarks as attacks?', 'type': 'bool'},
        {'id': 'scid18', 'text': 'Do you engage in self-damaging acts or have recurrent suicidal behavior?', 'type': 'bool'},
        {'id': 'scid19', 'text': 'Do you avoid making decisions without excessive advice and reassurance?', 'type': 'bool'},
        {'id': 'scid20', 'text': 'Are you preoccupied with fantasies of unlimited success, power, brilliance, or beauty?', 'type': 'bool'},
        {'id': 'scid21', 'text': 'Do you have unstable self-image or sense of self?', 'type': 'bool'},
        {'id': 'scid22', 'text': 'Do you often act in ways that are reckless or show little regard for safety?', 'type': 'bool'},
        {'id': 'scid23', 'text': 'Do you feel constrained by rules and prefer flexibility to structure?', 'type': 'bool'},
        {'id': 'scid24', 'text': 'Do you find it hard to discard worn-out or worthless items even with no sentimental value?', 'type': 'bool'},
    ]
    return items


@assessments_bp.route('/')
@login_required
def assessments_index():
    return render_template('assessments/index.html')


@assessments_bp.route('/api/next_question', methods=['POST'])
@login_required
def next_question():
    payload = request.get_json(force=True) or {}
    instrument = payload.get('instrument', 'phq9')
    answers = payload.get('answers', [])  # list of {id, value}
    state = payload.get('state') or {}

    if instrument not in ('phq9', 'scid5pd'):
        return jsonify({'error': 'invalid instrument'}), 400

    if instrument == 'phq9':
        bank = _phq9_bank()
        id_to_item = {q['id']: q for q in bank}
        if not state.get('order'):
            order = [q['id'] for q in bank]
            random.shuffle(order)
            state['order'] = order
            state['index'] = 0
        # Branching: if item phq9 answered > 0, schedule a safety follow-up
        answered = {a['id']: a['value'] for a in answers}
        if 'phq9' in answered and answered['phq9'] and not state.get('safety_added'):
            state['safety_added'] = True
            # insert a follow-up immediately next
            state['order'].insert(state['index'] + 1, 'phq9_safety')
            id_to_item['phq9_safety'] = {
                'id': 'phq9_safety',
                'text': 'Have you had any thoughts or plans to harm yourself in the past two weeks?',
                'type': 'bool'
            }
        # Advance to next
        while state['index'] < len(state['order']):
            qid = state['order'][state['index']]
            if qid not in answered:
                item = id_to_item.get(qid)
                state['index'] += 1
                return jsonify({'question': item, 'state': state})
            state['index'] += 1
        # Completed -> score
        score = sum(int(v) for v in answered.values() if isinstance(v, (int, float)))
        severity = (
            'none-minimal' if score <= 4 else
            'mild' if score <= 9 else
            'moderate' if score <= 14 else
            'moderately severe' if score <= 19 else
            'severe'
        )
        # persist session
        try:
            sess = AssessmentSession(
                user_id=current_user.id,
                instrument='phq9',
                completed_at=datetime.utcnow(),
                score=score,
                severity=severity,
                answers_json=json.dumps(answers),
                state_json=json.dumps(state),
            )
            db.session.add(sess)
            db.session.commit()
        except Exception:
            db.session.rollback()
        return jsonify({'done': True, 'score': score, 'severity': severity, 'state': state})

    # SCID-5-PD screening logic
    bank = _scid5pd_bank()
    id_to_item = {q['id']: q for q in bank}
    if not state.get('order'):
        # select at least 20 questions randomly
        ids = [q['id'] for q in bank]
        random.shuffle(ids)
        state['order'] = ids[:max(20, len(ids))] if len(ids) >= 20 else ids
        state['index'] = 0
    answered = {a['id']: a['value'] for a in answers}

    # Branching examples: if scid8 (borderline) yes, add follow-up on self-harm if not already asked
    if answered.get('scid8') is True and 'scid8_follow' not in answered and not state.get('scid8_follow_added'):
        state['scid8_follow_added'] = True
        state['order'].insert(state['index'] + 1, 'scid8_follow')
        id_to_item['scid8_follow'] = {
            'id': 'scid8_follow',
            'text': 'Have mood changes led to impulsive acts or self-harm?',
            'type': 'bool'
        }

    # Iterate to next unanswered question
    while state['index'] < len(state['order']):
        qid = state['order'][state['index']]
        if qid not in answered:
            item = id_to_item.get(qid)
            state['index'] += 1
            return jsonify({'question': item, 'state': state})
        state['index'] += 1

    # Finished: return simple domain tallies
    positive = sum(1 for k, v in answered.items() if str(k).startswith('scid') and v is True)
    risk_flag = any(answered.get(k) for k in ('scid8_follow', 'scid18'))
    try:
        sess = AssessmentSession(
            user_id=current_user.id,
            instrument='scid5pd',
            completed_at=datetime.utcnow(),
            positives=positive,
            risk_flag=risk_flag,
            answers_json=json.dumps(answers),
            state_json=json.dumps(state),
        )
        db.session.add(sess)
        db.session.commit()
    except Exception:
        db.session.rollback()
    return jsonify({'done': True, 'positives': positive, 'risk_flag': risk_flag, 'state': state})


# Chatbot Blueprint
chat_bp = Blueprint('chat', __name__, url_prefix='/chat')


@chat_bp.route('/')
@login_required
def chat_index():
    return render_template('chat/index.html')


@chat_bp.route('/api/message', methods=['POST'])
@login_required
def chat_message():
    data = request.get_json(force=True) or {}
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'error': 'empty'}), 400
    # Use simple analyzer placeholder
    try:
        from ml_services import analyze_sentiment
        analysis = analyze_sentiment(text)
    except Exception:
        analysis = {'sentiment': 'neutral', 'confidence': 0.5}

    sentiment = analysis.get('sentiment', 'neutral')

    # --- Conversational branching helpers ---
    def detect_topics(t: str) -> List[str]:
        t = t.lower()
        topics = []
        mapping = {
            'anxiety': ['anxious','panic','worry','racing heart','restless','nervous'],
            'depression': ['depressed','down','hopeless','worthless','no interest','tired','fatigue'],
            'sleep': ['sleep','insomnia','awake','tired','nightmare','can\'t sleep'],
            'stress': ['stress','stressed','overwhelmed','pressure','burnout'],
            'self_harm': ['suicide','kill myself','self-harm','harm myself','end my life'],
            'substance': ['alcohol','drink too much','drugs','substance','weed','cocaine']
        }
        for key, kws in mapping.items():
            if any(k in t for k in kws):
                topics.append(key)
        return topics or ['general']

    def topic_suggestions(topic: str) -> List[str]:
        suggestions = {
            'anxiety': [
                'Try box breathing: inhale 4s, hold 4s, exhale 4s, hold 4s (4 cycles).',
                'Yoga: Child\'s Pose (Balasana) 60–90s, Seated Forward Fold (Paschimottanasana) 60s.',
                'Grounding: Name 5 things you can see, 4 feel, 3 hear, 2 smell, 1 taste.'
            ],
            'depression': [
                'Brief activation: 10–15 min walk or light stretching.',
                'Journaling: Write 3 small tasks you can complete today.',
                'Sleep hygiene: fixed wake time; no screens 60 min before bed.'
            ],
            'sleep': [
                'Wind-down: dim lights, avoid caffeine 6h before bed.',
                '4‑7‑8 breathing for 3–4 cycles.',
                'Yoga: Legs Up the Wall (Viparita Karani) 2–3 min.'
            ],
            'stress': [
                'Micro-break: 5 min of diaphragmatic breathing.',
                'Time-box one task for 20 min; reduce multitasking.',
                'Neck/shoulder release: gentle rolls for 60s.'
            ],
            'substance': [
                'Delay/Distraction: wait 20 min and do a different activity.',
                'Track triggers and plan an alternative response.',
                'Hydrate and eat before social events to reduce cue‑reactivity.'
            ],
            'general': [
                '3 deep breaths; slow your exhale.',
                'Short walk in fresh air.',
                'Message a supportive friend.'
            ]
        }
        return suggestions.get(topic, suggestions['general'])

    def topic_specialist(topic: str) -> str:
        return {
            'anxiety': 'Psychiatrist',
            'depression': 'Psychiatrist',
            'sleep': 'Sleep Medicine Psychiatrist',
            'stress': 'Psychologist',
            'substance': 'Addiction Psychiatrist',
            'self_harm': 'Crisis & Psychiatry',
            'general': 'Psychologist'
        }.get(topic, 'Psychologist')

    # Retrieve or init conversation state
    state_key = f"chat_state_{current_user.id}"
    state = session.get(state_key) or {'stage': 'intro', 'topic': None, 'neg_count': 0}

    lowered = text.lower()
    topics = detect_topics(lowered)
    primary_topic = topics[0]

    # Risk checks
    risk_flag = ('self_harm' in topics)
    strong_negative = (sentiment == 'negative' and float(analysis.get('confidence', 0.0)) >= 0.6)
    last_phq9 = AssessmentSession.query.filter_by(user_id=current_user.id, instrument='phq9').order_by(AssessmentSession.completed_at.desc()).first()
    last_scid = AssessmentSession.query.filter_by(user_id=current_user.id, instrument='scid5pd').order_by(AssessmentSession.completed_at.desc()).first()
    phq_severe = bool(last_phq9 and (last_phq9.severity in ('severe','moderately severe') or (last_phq9.score or 0) >= 15))
    scid_risk = bool(last_scid and last_scid.risk_flag)

    if sentiment == 'negative':
        state['neg_count'] = state.get('neg_count', 0) + 1

    # Branching
    quick_replies: List[str] = []
    doctors: List[Dict[str, Any]] = []

    if state['stage'] == 'intro':
        reply = "I’m here with you. What’s troubling you most right now?"
        quick_replies = ['Anxiety', 'Low mood', 'Sleep', 'Stress']
        state['stage'] = 'collect'
    elif risk_flag:
        reply = ("It sounds like you might be at risk. If you’re in immediate danger, call your local emergency number now. "
                 "I can also connect you to nearby professionals.")
        state['stage'] = 'escalate'
    elif strong_negative or state.get('neg_count', 0) >= 3 or phq_severe or scid_risk:
        reply = ("Thanks for sharing. Given what you’ve said, I recommend speaking with a specialist. Would you like some options?")
        state['stage'] = 'escalate'
    else:
        # Self‑care coaching
        state['topic'] = state.get('topic') or primary_topic
        tips = topic_suggestions(state['topic'])
        reply = f"Let’s try a quick step for {state['topic']}: {tips[0]}"
        quick_replies = ['More tips', 'Show yoga steps', 'Talk to a professional']
        state['stage'] = 'coach'

    # If escalate, suggest specialists
    if state['stage'] == 'escalate':
        spec = topic_specialist(primary_topic)
        reply = reply + f" Recommended specialist: {spec}."
        doctors = [
            {
                'name': 'Dr. Sarah Johnson, MD', 'specialty': 'Psychiatrist — Depression & Anxiety', 'distance': '0.5 miles', 'next_available': 'Tomorrow 2:00 PM', 'phone': '(617) 555-0123', 'address': '123 Main Street, Boston, MA'
            },
            {
                'name': 'Dr. Michael Chen, MD', 'specialty': 'Child & Adolescent Psychiatry', 'distance': '1.2 miles', 'next_available': 'Today 4:00 PM', 'phone': '(617) 555-0456', 'address': '456 Oak Avenue, Cambridge, MA'
            },
            {
                'name': 'Dr. Emily Rodriguez, PhD', 'specialty': 'Psychologist — Trauma & PTSD', 'distance': '2.1 miles', 'next_available': 'Next Week', 'phone': '(617) 555-0789', 'address': '789 Pine Road, Somerville, MA'
            },
        ]
        quick_replies = ['Call first option', 'View all professionals']

    # Save state in session
    session[state_key] = state

    # persist user and bot messages
    try:
        db.session.add(ChatMessage(user_id=current_user.id, role='user', text=text))
        db.session.add(ChatMessage(user_id=current_user.id, role='bot', text=reply, sentiment=sentiment, confidence=analysis.get('confidence', 0.5)))
        db.session.commit()
    except Exception:
        db.session.rollback()
    return jsonify({
        'sentiment': sentiment,
        'confidence': analysis.get('confidence', 0.5),
        'reply': reply,
        'doctors': doctors,
        'escalate': escalate,
        'quick_replies': quick_replies,
    })


