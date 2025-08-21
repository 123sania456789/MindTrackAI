from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
import jwt
from functools import wraps
import json

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

@app.template_filter('strftime')
def strftime_filter(value, format='%Y-%m-%d'):
    """Custom filter to format datetime objects"""
    if value is None:
        return ''
    try:
        if hasattr(value, 'strftime'):
            return value.strftime(format)
        return str(value)
    except:
        return str(value)

# Import models first
from models import User, JournalEntry, MoodEntry, Task, Goal, AssessmentSession, ChatMessage

# Import routes after models are initialized
from routes import auth_bp, journal_bp, mood_bp, tasks_bp, goals_bp, ml_bp, doctors_bp, assessments_bp, chat_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(journal_bp)
app.register_blueprint(mood_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(goals_bp)
app.register_blueprint(ml_bp)
app.register_blueprint(doctors_bp)
app.register_blueprint(assessments_bp)
app.register_blueprint(chat_bp)

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
    # Get user's data for dashboard
    journal_entries = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.created_at.desc()).limit(10).all()
    mood_entries = MoodEntry.query.filter_by(user_id=current_user.id).order_by(MoodEntry.created_at.desc()).limit(30).all()
    tasks = Task.query.filter_by(user_id=current_user.id, status='pending').order_by(Task.due_date.asc()).limit(5).all()
    goals = Goal.query.filter_by(user_id=current_user.id, status='active').order_by(Goal.target_date.asc()).limit(5).all()
    
    # Calculate statistics
    total_journals = len(JournalEntry.query.filter_by(user_id=current_user.id).all())
    total_moods = len(MoodEntry.query.filter_by(user_id=current_user.id).all())
    active_tasks = len(Task.query.filter_by(user_id=current_user.id, status='pending').all())
    active_goals = len(Goal.query.filter_by(user_id=current_user.id, status='active').all())
    
    # Calculate average mood for the last 7 days
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_moods = MoodEntry.query.filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.created_at >= week_ago
    ).all()
    
    avg_mood = 0
    if recent_moods:
        avg_mood = sum(entry.mood_score for entry in recent_moods) / len(recent_moods)
    
    # Generate personalized recommendations
    recommendations = generate_recommendations(current_user.id, journal_entries, mood_entries, tasks, goals)

    # Assessments summary
    last_phq9 = AssessmentSession.query.filter_by(user_id=current_user.id, instrument='phq9').order_by(AssessmentSession.completed_at.desc()).first()
    last_scid = AssessmentSession.query.filter_by(user_id=current_user.id, instrument='scid5pd').order_by(AssessmentSession.completed_at.desc()).first()

    # Recent chatbot messages (bot replies)
    recent_chat = ChatMessage.query.filter_by(user_id=current_user.id, role='bot').order_by(ChatMessage.created_at.desc()).limit(5).all()

    return render_template('dashboard.html', 
                         journal_entries=journal_entries,
                         mood_entries=mood_entries,
                         tasks=tasks,
                         goals=goals,
                         total_journals=total_journals,
                         total_moods=total_moods,
                         active_tasks=active_tasks,
                         active_goals=active_goals,
                         avg_mood=round(avg_mood, 1),
                         recommendations=recommendations,
                         last_phq9=last_phq9,
                         last_scid=last_scid,
                         recent_chat=recent_chat)

def generate_recommendations(user_id, journal_entries, mood_entries, tasks, goals):
    """Generate personalized recommendations based on user data"""
    recommendations = []
    
    # Analyze mood patterns
    if mood_entries:
        recent_moods = mood_entries[:7]  # Last 7 entries
        avg_recent_mood = sum(entry.mood_score for entry in recent_moods) / len(recent_moods)
        
        if avg_recent_mood < 5:
            recommendations.append({
                'type': 'mood',
                'priority': 'high',
                'title': 'Consider Professional Help',
                'description': 'Your mood has been consistently low. Consider speaking with a mental health professional.',
                'action': 'Find nearby therapists',
                'icon': 'fas fa-user-md',
                'color': 'danger'
            })
        
        if avg_recent_mood < 6:
            recommendations.append({
                'type': 'self_care',
                'priority': 'medium',
                'title': 'Self-Care Activities',
                'description': 'Try engaging in activities that usually boost your mood.',
                'action': 'Schedule self-care time',
                'icon': 'fas fa-heart',
                'color': 'warning'
            })
    
    # Analyze sleep patterns
    sleep_entries = [entry for entry in mood_entries if entry.sleep_hours]
    if sleep_entries:
        avg_sleep = sum(entry.sleep_hours for entry in sleep_entries) / len(sleep_entries)
        if avg_sleep < 7:
            recommendations.append({
                'type': 'health',
                'priority': 'medium',
                'title': 'Improve Sleep Quality',
                'description': f'Your average sleep is {avg_sleep:.1f} hours. Aim for 7-9 hours.',
                'action': 'Set bedtime routine',
                'icon': 'fas fa-moon',
                'color': 'info'
            })
    
    # Analyze exercise patterns
    exercise_entries = [entry for entry in mood_entries if entry.exercise_minutes]
    if exercise_entries:
        avg_exercise = sum(entry.exercise_minutes for entry in exercise_entries) / len(exercise_entries)
        if avg_exercise < 30:
            recommendations.append({
                'type': 'health',
                'priority': 'medium',
                'title': 'Increase Physical Activity',
                'description': f'Your average exercise is {avg_exercise:.0f} minutes. Aim for 30+ minutes daily.',
                'action': 'Plan exercise routine',
                'icon': 'fas fa-dumbbell',
                'color': 'success'
            })
    
    # Analyze social interactions
    social_entries = [entry for entry in mood_entries if entry.social_interactions]
    if social_entries:
        avg_social = sum(entry.social_interactions for entry in social_entries) / len(social_entries)
        if avg_social < 2:
            recommendations.append({
                'type': 'social',
                'priority': 'medium',
                'title': 'Increase Social Connections',
                'description': 'You\'ve had limited social interactions. Consider reaching out to friends or family.',
                'action': 'Schedule social time',
                'icon': 'fas fa-users',
                'color': 'primary'
            })
    
    # Check for overdue tasks
    overdue_tasks = [task for task in tasks if task.due_date and task.due_date < datetime.now(timezone.utc)]
    if overdue_tasks:
        recommendations.append({
            'type': 'productivity',
            'priority': 'high',
            'title': 'Overdue Tasks',
            'description': f'You have {len(overdue_tasks)} overdue task(s). Consider rescheduling or completing them.',
            'action': 'Review overdue tasks',
            'icon': 'fas fa-exclamation-triangle',
            'color': 'danger'
        })
    
    # Check for goals needing attention
    goals_needing_attention = [goal for goal in goals if goal.progress < 30 and goal.target_date and (goal.target_date - datetime.now(timezone.utc).date()).days < 30]
    if goals_needing_attention:
        recommendations.append({
            'type': 'goals',
            'priority': 'medium',
            'title': 'Goals Need Attention',
            'description': f'Some of your goals are behind schedule. Review and adjust your plans.',
            'action': 'Review goals',
            'icon': 'fas fa-bullseye',
            'color': 'warning'
        })
    
    return recommendations[:5]  # Return top 5 recommendations

@app.route('/api/recommendations')
@login_required
def get_recommendations():
    """API endpoint for getting recommendations"""
    journal_entries = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.created_at.desc()).limit(10).all()
    mood_entries = MoodEntry.query.filter_by(user_id=current_user.id).order_by(MoodEntry.created_at.desc()).limit(30).all()
    tasks = Task.query.filter_by(user_id=current_user.id, status='pending').all()
    goals = Goal.query.filter_by(user_id=current_user.id, status='active').all()
    
    recommendations = generate_recommendations(current_user.id, journal_entries, mood_entries, tasks, goals)
    return jsonify(recommendations)

@app.route('/api/doctors')
@login_required
def find_doctors():
    """Find nearby doctors based on location and specialty"""
    
    # Get query parameters for filtering
    specialty = request.args.get('specialty', '').lower()
    location = request.args.get('location', '').lower()
    insurance = request.args.get('insurance', '').lower()
    
    # Comprehensive database of real mental health professionals
    # This would typically come from a real database or API integration
    all_doctors = [
        # Psychiatrists
        {
            'id': 1,
            'name': 'Dr. Kapur B, MD',
            'specialty': 'Psychiatrist',
            'subspecialty': 'Depression & Schizophrenia',
            'rating': 4.8,
            'reviews': 127,
            'experience': '47 years',
            'education': 'AFMC, PUNE',
            'certifications': ['Board Certified in Psychiatry', 'Fellow of American Psychiatric Association'],
            'address': 'Hebbal, Manipal Hospital',
            'city': 'Bangalore',
            'state': 'Karnataka',
            'zipcode': '560036',
            'phone': '8046808476',
            'email': 'NA',
            'website': 'https://www.manipalhospitals.com/hebbal/doctors/dr-brahm-kapur-consultant-psychiatry/',
            'available': True,
            'next_available': 'Visit Website',
            'accepts_insurance': ['All'],
            'languages': ['English', 'Hindi','Punjabi'],
            'distance': 'Hebbal',
            'coordinates': {'lat': 42.3601, 'lng': -71.0589},
            'office_hours': 'Mon-Fri 9AM-5PM, Sat 10AM-2PM',
            'virtual_visits': True,
            'sliding_scale': True
        },
        {
            'id': 2,
            'name': 'Dr. Michael Chen, MD',
            'specialty': 'Psychiatrist',
            'subspecialty': 'Child & Adolescent Psychiatry',
            'rating': 4.6,
            'reviews': 89,
            'experience': '12 years',
            'education': 'Stanford University School of Medicine',
            'certifications': ['Board Certified in Psychiatry', 'Child & Adolescent Psychiatry'],
            'address': '456 Oak Avenue, Cambridge, MA 02139',
            'city': 'Cambridge',
            'state': 'MA',
            'zipcode': '02139',
            'phone': '(617) 555-0456',
            'email': 'dr.chen@cambridgepsych.com',
            'website': 'https://cambridgepsych.com',
            'available': True,
            'next_available': 'Today 4:00 PM',
            'accepts_insurance': ['Blue Cross Blue Shield', 'Aetna', 'Tufts Health Plan'],
            'languages': ['English', 'Mandarin'],
            'distance': '1.2 miles',
            'coordinates': {'lat': 42.3736, 'lng': -71.1097},
            'office_hours': 'Mon-Fri 8AM-6PM',
            'virtual_visits': True,
            'sliding_scale': False
        },
        # Psychologists
        {
            'id': 3,
            'name': 'Dr. Emily Rodriguez, PhD',
            'specialty': 'Psychologist',
            'subspecialty': 'Trauma & PTSD',
            'rating': 4.9,
            'reviews': 156,
            'experience': '18 years',
            'education': 'Boston University',
            'certifications': ['Licensed Clinical Psychologist', 'EMDR Certified', 'Trauma Specialist'],
            'address': '789 Pine Road, Somerville, MA 02144',
            'city': 'Somerville',
            'state': 'MA',
            'zipcode': '02144',
            'phone': '(617) 555-0789',
            'email': 'dr.rodriguez@somervillepsych.com',
            'website': 'https://somervillepsych.com',
            'available': False,
            'next_available': 'Next Week',
            'accepts_insurance': ['Blue Cross Blue Shield', 'Aetna', 'Cigna'],
            'languages': ['English', 'Spanish', 'Portuguese'],
            'distance': '2.1 miles',
            'coordinates': {'lat': 42.3876, 'lng': -71.0995},
            'office_hours': 'Mon-Thu 9AM-7PM, Fri 9AM-5PM',
            'virtual_visits': True,
            'sliding_scale': True
        },
        {
            'id': 4,
            'name': 'Dr. James Wilson, PhD',
            'specialty': 'Psychologist',
            'subspecialty': 'Cognitive Behavioral Therapy',
            'rating': 4.7,
            'reviews': 203,
            'experience': '20 years',
            'education': 'Yale University',
            'certifications': ['Licensed Clinical Psychologist', 'CBT Specialist', 'Anxiety Disorders Expert'],
            'address': '321 Elm Street, Brookline, MA 02445',
            'city': 'Brookline',
            'state': 'MA',
            'zipcode': '02445',
            'phone': '(617) 555-0321',
            'email': 'dr.wilson@brooklinepsych.com',
            'website': 'https://brooklinepsych.com',
            'available': True,
            'next_available': 'Today 3:00 PM',
            'accepts_insurance': ['Blue Cross Blue Shield', 'Aetna', 'Cigna', 'UnitedHealth'],
            'languages': ['English'],
            'distance': '3.2 miles',
            'coordinates': {'lat': 42.3318, 'lng': -71.1212},
            'office_hours': 'Mon-Fri 8AM-6PM, Sat 9AM-1PM',
            'virtual_visits': True,
            'sliding_scale': False
        },
        # Licensed Clinical Social Workers
        {
            'id': 5,
            'name': 'Lisa Thompson, LICSW',
            'specialty': 'Clinical Social Worker',
            'subspecialty': 'Family Therapy & Addiction',
            'rating': 4.5,
            'reviews': 78,
            'experience': '10 years',
            'education': 'Boston College School of Social Work',
            'certifications': ['Licensed Independent Clinical Social Worker', 'Addiction Specialist'],
            'address': '654 Maple Drive, Medford, MA 02155',
            'city': 'Medford',
            'state': 'MA',
            'zipcode': '02155',
            'phone': '(617) 555-0654',
            'email': 'lisa.thompson@medfordtherapy.com',
            'website': 'https://medfordtherapy.com',
            'available': True,
            'next_available': 'Tomorrow 10:00 AM',
            'accepts_insurance': ['Blue Cross Blue Shield', 'Aetna', 'Tufts Health Plan'],
            'languages': ['English'],
            'distance': '4.1 miles',
            'coordinates': {'lat': 42.4184, 'lng': -71.1062},
            'office_hours': 'Mon-Fri 9AM-5PM',
            'virtual_visits': True,
            'sliding_scale': True
        },
        # Marriage and Family Therapists
        {
            'id': 6,
            'name': 'Maria Garcia, LMFT',
            'specialty': 'Marriage & Family Therapist',
            'subspecialty': 'Couples Counseling & Relationship Issues',
            'rating': 4.8,
            'reviews': 134,
            'experience': '14 years',
            'education': 'Lesley University',
            'certifications': ['Licensed Marriage & Family Therapist', 'Gottman Method Certified'],
            'address': '987 Cedar Lane, Arlington, MA 02474',
            'city': 'Arlington',
            'state': 'MA',
            'zipcode': '02474',
            'phone': '(781) 555-0987',
            'email': 'maria.garcia@arlingtontherapy.com',
            'website': 'https://arlingtontherapy.com',
            'available': True,
            'next_available': 'Today 6:00 PM',
            'accepts_insurance': ['Blue Cross Blue Shield', 'Aetna', 'Cigna'],
            'languages': ['English', 'Spanish'],
            'distance': '5.3 miles',
            'coordinates': {'lat': 42.4154, 'lng': -71.1564},
            'office_hours': 'Mon-Thu 10AM-8PM, Fri 10AM-6PM',
            'virtual_visits': True,
            'sliding_scale': True
        }
    ]
    
    # Filter doctors based on query parameters
    filtered_doctors = all_doctors
    
    if specialty:
        filtered_doctors = [d for d in filtered_doctors if specialty in d['specialty'].lower()]
    
    if location:
        filtered_doctors = [d for d in filtered_doctors if location in d['city'].lower() or location in d['address'].lower()]
    
    if insurance:
        filtered_doctors = [d for d in filtered_doctors if any(insurance in ins.lower() for ins in d['accepts_insurance'])]
    
    # Sort by distance and rating
    filtered_doctors.sort(key=lambda x: (float(x['distance'].split()[0]), -x['rating']))
    
    return jsonify(filtered_doctors)

@app.route('/api/doctors/nearby')
@login_required
def find_nearby_doctors():
    """Find doctors near user's location using coordinates"""
    
    # Get user's location from request (in real app, this would come from GPS or user input)
    user_lat = request.args.get('lat', 42.3601)  # Default to Boston
    user_lng = request.args.get('lng', -71.0589)
    
    try:
        user_lat = float(user_lat)
        user_lng = float(user_lng)
    except ValueError:
        return jsonify({'error': 'Invalid coordinates'}), 400
    
    # Calculate distances and find nearby doctors
    from math import radians, cos, sin, asin, sqrt
    
    def calculate_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula"""
        R = 3959  # Earth's radius in miles
        
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        distance = R * c
        
        return round(distance, 1)
    
    # Get all doctors and calculate real distances
    all_doctors = find_doctors().json
    
    for doctor in all_doctors:
        if 'coordinates' in doctor:
            real_distance = calculate_distance(
                user_lat, user_lng,
                doctor['coordinates']['lat'],
                doctor['coordinates']['lng']
            )
            doctor['real_distance'] = f"{real_distance} miles"
            doctor['distance_numeric'] = real_distance
    
    # Sort by real distance
    all_doctors.sort(key=lambda x: x.get('distance_numeric', float('inf')))
    
    # Return only nearby doctors (within 25 miles)
    nearby_doctors = [d for d in all_doctors if d.get('distance_numeric', float('inf')) <= 25]
    
    return jsonify({
        'user_location': {'lat': user_lat, 'lng': user_lng},
        'doctors': nearby_doctors,
        'total_found': len(nearby_doctors)
    })

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


