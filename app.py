# app.py - Main Flask Application
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
import os
import json
import anthropic
from functools import wraps
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///mind_shelter.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize Anthropic client
anthropic_client = anthropic.Anthropic(
    api_key=os.environ.get('ANTHROPIC_API_KEY', 'your-anthropic-api-key-here')
)

# Database Models
class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    preferences = db.relationship('UserPreferences', backref='user', uselist=False)
    sessions = db.relationship('SessionParticipant', backref='user')

class Realm(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    focus_outcome = db.Column(db.String(50), nullable=True)  # ADDED THIS LINE
    color_scheme = db.Column(db.String(50), nullable=True)
    metaphors = db.Column(db.Text, nullable=True)  # JSON string
    icebreaker_prompts = db.Column(db.Text, nullable=True)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Session(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    realm_id = db.Column(db.String(36), db.ForeignKey('realm.id'), nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in_progress, completed, cancelled
    duration_minutes = db.Column(db.Integer, default=15)
    room_code = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    realm = db.relationship('Realm', backref='sessions')
    participants = db.relationship('SessionParticipant', backref='session')

class SessionParticipant(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('session.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    pre_session_mood = db.Column(db.Integer, nullable=True)  # 1-10
    post_session_mood = db.Column(db.Integer, nullable=True)  # 1-10
    session_rating = db.Column(db.Integer, nullable=True)  # 1-5 stars
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserPreferences(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    user_type = db.Column(db.String(50), default='university_student')
    subscription_type = db.Column(db.String(20), default='none')
    ambient_sounds_enabled = db.Column(db.Boolean, default=True)
    completed_sessions = db.Column(db.Integer, default=0)
    timezone = db.Column(db.String(50), nullable=True)
    preferred_session_times = db.Column(db.Text, nullable=True)  # JSON string

# Add these new models to app.py after existing models

class MoodEntry(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    mood_score = db.Column(db.Integer, nullable=False)  # 1-10 scale
    focus_area = db.Column(db.String(50), nullable=False)  # anxiety, sleep, work_stress
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='mood_entries')

class UserProgress(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    total_sessions = db.Column(db.Integer, default=0)
    badges_earned = db.Column(db.Text, nullable=True)  # JSON array
    anxiety_trend = db.Column(db.Float, nullable=True)  # percentage change
    sleep_trend = db.Column(db.Float, nullable=True)
    work_stress_trend = db.Column(db.Float, nullable=True)
    last_session_date = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    user = db.relationship('User', backref='progress', uselist=False)

# Helper Functions
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def seed_outcome_realms():
    """Replace metaphor-based realms with outcome-focused ones"""
    # Clear existing realms
    Realm.query.delete()
    
    outcome_realms = [
        {
            'name': 'Calm Mind',
            'description': 'Share stories about managing daily anxiety and finding peace',
            'category': 'anxiety',
            'focus_outcome': 'anxiety_reduction'
        },
        {
            'name': 'Restful Nights',
            'description': 'Connect over sleep struggles and discover what helps you rest',
            'category': 'sleep',
            'focus_outcome': 'sleep_improvement'
        },
        {
            'name': 'Work Balance',
            'description': 'Discuss work pressures and share healthy coping strategies',
            'category': 'work_stress',
            'focus_outcome': 'stress_management'
        },
        {
            'name': 'Daily Wins',
            'description': 'Celebrate small victories and build positive momentum',
            'category': 'positivity',
            'focus_outcome': 'mood_boost'
        }
    ]
    
    for realm_data in outcome_realms:
        realm = Realm(**realm_data)
        db.session.add(realm)
    
    db.session.commit()

def generate_metaphors_with_anthropic(realm_name, realm_description):
    """Generate metaphors using Anthropic API"""
    try:
        message = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": f"""Generate 3 unique and profound figurative language prompts (metaphors, similes, or personification) 
                    for the theme "{realm_name}" which is about "{realm_description}". 
                    
                    These should be introspective, emotionally resonant, and help people connect with their inner experience related to this theme.
                    Each should be 8-15 words long and capture different aspects of the human experience within this realm.
                    
                    Make them poetic and meaningful - these will help match people with similar emotional states and perspectives.
                    
                    Return your response as a JSON object with this structure:
                    {{
                        "metaphors": [
                            {{"text": "example metaphor text", "type": "metaphor"}},
                            {{"text": "example simile text", "type": "simile"}},
                            {{"text": "example personification text", "type": "personification"}}
                        ]
                    }}"""
                }
            ]
        )
        
        response_text = message.content[0].text
        # Try to parse JSON from the response
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If JSON parsing fails, extract metaphors manually
            return {
                "metaphors": [
                    {"text": f"Generated metaphor for {realm_name}", "type": "metaphor"},
                    {"text": f"Life feels like navigating through {realm_name.lower()}", "type": "simile"},
                    {"text": f"{realm_name} whispers secrets of growth", "type": "personification"}
                ]
            }
    except Exception as e:
        print(f"Error generating metaphors: {e}")
        # Return fallback metaphors
        return {
            "metaphors": [
                {"text": f"Exploring the depths of {realm_name.lower()}", "type": "metaphor"},
                {"text": f"Like walking through {realm_name.lower()}", "type": "simile"},
                {"text": f"{realm_name} calls to our inner wisdom", "type": "personification"}
            ]
        }

def generate_icebreaker_with_anthropic(realm_name, metaphor_text):
    """Generate personalized icebreaker using Anthropic API"""
    try:
        message = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": f"""Based on the theme "{realm_name}" and the selected metaphor: "{metaphor_text}", 
                    generate a thoughtful, personal reflection prompt that invites deep sharing and connection. 
                    The question should be open-ended, emotionally resonant, and help the person share a meaningful personal experience related to this theme.
                    Keep it to one sentence and make it conversational.
                    
                    Return your response as a JSON object:
                    {{"icebreaker": "your generated prompt here"}}"""
                }
            ]
        )
        
        response_text = message.content[0].text
        try:
            result = json.loads(response_text)
            return result.get("icebreaker", f"Share a moment when you experienced {realm_name.lower()}, and what it taught you about yourself.")
        except json.JSONDecodeError:
            return f"Share a moment when you experienced {realm_name.lower()}, and what it taught you about yourself."
    except Exception as e:
        print(f"Error generating icebreaker: {e}")
        return f"Share a moment when you experienced {realm_name.lower()}, and what it taught you about yourself."

# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        full_name = data.get('full_name', 'User')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Find or create user
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, full_name=full_name)
            db.session.add(user)
            db.session.commit()
            
            # Create default preferences
            preferences = UserPreferences(user_id=user.id)
            db.session.add(preferences)
            db.session.commit()
        
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = user.full_name
        
        if request.is_json:
            return jsonify({'success': True, 'redirect': url_for('home')})
        return redirect(url_for('home'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    realms = Realm.query.all()
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    # Get user preferences
    preferences = UserPreferences.query.filter_by(user_id=user_id).first()
    
    return render_template('home.html', realms=realms, user=user, preferences=preferences)

@app.route('/profile')
@login_required
def profile():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    preferences = UserPreferences.query.filter_by(user_id=user_id).first()
    
    return render_template('profile.html', user=user, preferences=preferences)

@app.route('/sessions')
@login_required
def sessions():
    user_id = session.get('user_id')
    
    # Get user's sessions
    user_sessions = db.session.query(Session).join(SessionParticipant).filter(
        SessionParticipant.user_id == user_id
    ).order_by(Session.scheduled_time.desc()).all()
    
    realms = {realm.id: realm for realm in Realm.query.all()}
    
    return render_template('sessions.html', sessions=user_sessions, realms=realms)

@app.route('/metaphor-flow')
@login_required
def metaphor_flow():
    realm_id = request.args.get('realm')
    if not realm_id:
        return redirect(url_for('home'))
    
    realm = Realm.query.get(realm_id)
    if not realm:
        return redirect(url_for('home'))
    
    return render_template('metaphor_flow.html', realm=realm)

@app.route('/session-lobby')
@login_required
def session_lobby():
    session_id = request.args.get('session')
    if not session_id:
        return redirect(url_for('home'))
    
    session_obj = Session.query.get(session_id)
    if not session_obj:
        return redirect(url_for('home'))
    
    return render_template('session_lobby.html', session=session_obj)

@app.route('/live-session')
@login_required
def live_session():
    session_id = request.args.get('session')
    if not session_id:
        return redirect(url_for('home'))
    
    session_obj = Session.query.get(session_id)
    if not session_obj:
        return redirect(url_for('home'))
    
    return render_template('live_session.html', session=session_obj)

# API Routes
@app.route('/api/generate-metaphors', methods=['POST'])
@login_required
def api_generate_metaphors():
    data = request.get_json()
    realm_id = data.get('realm_id')
    
    realm = Realm.query.get(realm_id)
    if not realm:
        return jsonify({'error': 'Realm not found'}), 404
    
    metaphors_data = generate_metaphors_with_anthropic(realm.name, realm.description)
    return jsonify(metaphors_data)

@app.route('/api/create-session', methods=['POST'])
@login_required
def api_create_session():
    data = request.get_json()
    realm_id = data.get('realm_id')
    chosen_metaphor = data.get('chosen_metaphor')
    
    realm = Realm.query.get(realm_id)
    if not realm:
        return jsonify({'error': 'Realm not found'}), 404
    
    # First, try to find an existing session that's not full (less than 5 participants)
    existing_session = db.session.query(Session).join(SessionParticipant).filter(
        Session.realm_id == realm_id,
        Session.status == 'scheduled',
        Session.scheduled_time > datetime.utcnow()
    ).group_by(Session.id).having(
        db.func.count(SessionParticipant.id) < 5
    ).first()
    
    if existing_session:
        # Join existing session
        participant = SessionParticipant(
    session_id=existing_session.id,
    user_id=session['user_id']
    )
        db.session.add(participant)
        db.session.commit()
        
        return jsonify({
            'session_id': existing_session.id,
            'room_code': existing_session.room_code,
            'scheduled_time': existing_session.scheduled_time.isoformat()
        })
    
    # If no existing session with space, create new one
    # Generate icebreaker prompt
    icebreaker = generate_icebreaker_with_anthropic(realm.name, chosen_metaphor)
    
    # Create session (unlimited number allowed)
    room_code = str(uuid.uuid4())[:8].upper()
    new_session = Session(
        realm_id=realm_id,
        scheduled_time=datetime.utcnow() + timedelta(minutes=2),
        room_code=room_code
    )
    db.session.add(new_session)
    db.session.flush()
    
    # Add participant
    participant = SessionParticipant(
    session_id=new_session.id,
    user_id=session['user_id']
    )
    db.session.add(participant)
    db.session.commit()
    
    return jsonify({
        'session_id': new_session.id,
        'room_code': room_code,
        'scheduled_time': new_session.scheduled_time.isoformat()
    })

@app.route('/api/update-preferences', methods=['POST'])
@login_required
def api_update_preferences():
    data = request.get_json()
    user_id = session['user_id']
    
    preferences = UserPreferences.query.filter_by(user_id=user_id).first()
    if not preferences:
        preferences = UserPreferences(user_id=user_id)
    
    # Update fields
    if 'user_type' in data:
        preferences.user_type = data['user_type']
    if 'timezone' in data:
        preferences.timezone = data['timezone']
    if 'ambient_sounds_enabled' in data:
        preferences.ambient_sounds_enabled = data['ambient_sounds_enabled']
    if 'subscription_type' in data:
        preferences.subscription_type = data['subscription_type']
    
    db.session.add(preferences)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/create-session-simple', methods=['POST'])
@login_required
def api_create_session_simple():
    data = request.get_json()
    realm_id = data.get('realm_id')
    mood_score = data.get('mood_score')
    focus_area = data.get('focus_area')
    notes = data.get('notes', '')
    
    realm = Realm.query.get(realm_id)
    if not realm:
        return jsonify({'error': 'Realm not found'}), 404
    
    # Record mood entry
    mood_entry = MoodEntry(
        user_id=session['user_id'],
        mood_score=mood_score,
        focus_area=focus_area,
        notes=notes
    )
    db.session.add(mood_entry)
    
    # Find or create session
    existing_session = db.session.query(Session).join(SessionParticipant).filter(
        Session.realm_id == realm_id,
        Session.status == 'scheduled',
        Session.scheduled_time > datetime.utcnow()
    ).group_by(Session.id).having(
        db.func.count(SessionParticipant.id) < 5
    ).first()
    
    if existing_session:
        # Join existing session
        participant = SessionParticipant(
            session_id=existing_session.id,
            user_id=session['user_id'],
            pre_session_mood=mood_score
        )
        db.session.add(participant)
        session_id = existing_session.id
        room_code = existing_session.room_code
        scheduled_time = existing_session.scheduled_time
    else:
        # Create new session
        room_code = str(uuid.uuid4())[:8].upper()
        new_session = Session(
            realm_id=realm_id,
            scheduled_time=datetime.utcnow() + timedelta(minutes=2),
            room_code=room_code
        )
        db.session.add(new_session)
        db.session.flush()
        
        participant = SessionParticipant(
            session_id=new_session.id,
            user_id=session['user_id'],
            pre_session_mood=mood_score
        )
        db.session.add(participant)
        session_id = new_session.id
        scheduled_time = new_session.scheduled_time
    
    # Update user progress
    progress = UserProgress.query.filter_by(user_id=session['user_id']).first()
    if not progress:
        progress = UserProgress(user_id=session['user_id'])
    
    # Update streak logic
    today = datetime.utcnow().date()
    if progress.last_session_date:
        days_diff = (today - progress.last_session_date.date()).days
        if days_diff == 1:
            progress.current_streak += 1
        elif days_diff > 1:
            progress.current_streak = 1
    else:
        progress.current_streak = 1
    
    progress.longest_streak = max(progress.longest_streak or 0, progress.current_streak)
    progress.total_sessions = (progress.total_sessions or 0) + 1
    progress.last_session_date = datetime.utcnow()
    
    # Award badges
    badges = json.loads(progress.badges_earned) if progress.badges_earned else []
    
    if progress.total_sessions == 1 and 'first_session' not in badges:
        badges.append('first_session')
    if progress.current_streak >= 7 and 'seven_day_streak' not in badges:
        badges.append('seven_day_streak')
    if progress.current_streak >= 30 and 'thirty_day_streak' not in badges:
        badges.append('thirty_day_streak')
    
    progress.badges_earned = json.dumps(badges)
    
    db.session.add(progress)
    db.session.commit()
    
    return jsonify({
        'session_id': session_id,
        'room_code': room_code,
        'scheduled_time': scheduled_time.isoformat()
    })

@app.route('/api/complete-session', methods=['POST'])
@login_required
def api_complete_session():
    data = request.get_json()
    session_id = data.get('session_id')
    post_mood = data.get('post_mood')
    rating = data.get('rating')
    
    participant = SessionParticipant.query.filter_by(
        session_id=session_id,
        user_id=session['user_id']
    ).first()
    
    if participant:
        participant.post_session_mood = post_mood
        participant.session_rating = rating
        
        # Update mood trends
        progress = UserProgress.query.filter_by(user_id=session['user_id']).first()
        if progress and participant.pre_session_mood and post_mood:
            mood_improvement = post_mood - participant.pre_session_mood
            if mood_improvement > 0:
                badges = json.loads(progress.badges_earned) if progress.badges_earned else []
                if 'mood_improver' not in badges:
                    badges.append('mood_improver')
                    progress.badges_earned = json.dumps(badges)
        
        db.session.commit()
    
    return jsonify({'success': True})

@app.route('/progress')
@login_required
def progress():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    # Get user progress
    user_progress = UserProgress.query.filter_by(user_id=user_id).first()
    if not user_progress:
        user_progress = UserProgress(user_id=user_id)
        db.session.add(user_progress)
        db.session.commit()
    
    # Calculate recent mood average
    recent_moods = MoodEntry.query.filter(
        MoodEntry.user_id == user_id,
        MoodEntry.created_at >= datetime.utcnow() - timedelta(days=7)
    ).all()
    
    recent_mood_avg = sum(m.mood_score for m in recent_moods) / len(recent_moods) if recent_moods else None
    
    # Get recent sessions
    recent_sessions = db.session.query(Session).join(SessionParticipant).filter(
        SessionParticipant.user_id == user_id,
        Session.status == 'completed'
    ).order_by(Session.scheduled_time.desc()).limit(5).all()
    
    # Calculate category averages
    anxiety_moods = [m for m in recent_moods if m.focus_area in ['anxiety', 'worry']]
    sleep_moods = [m for m in recent_moods if m.focus_area in ['falling_asleep', 'staying_asleep']]
    work_stress_moods = [m for m in recent_moods if m.focus_area in ['workload', 'boundaries']]
    
    anxiety_avg = sum(m.mood_score for m in anxiety_moods) / len(anxiety_moods) if anxiety_moods else None
    sleep_avg = sum(m.mood_score for m in sleep_moods) / len(sleep_moods) if sleep_moods else None
    work_stress_avg = sum(m.mood_score for m in work_stress_moods) / len(work_stress_moods) if work_stress_moods else None
    
    return render_template('progress.html', 
                         user=user, 
                         user_progress=user_progress,
                         recent_mood_avg=recent_mood_avg,
                         recent_sessions=recent_sessions,
                         anxiety_avg=anxiety_avg,
                         sleep_avg=sleep_avg,
                         work_stress_avg=work_stress_avg)

@app.route('/mood-checkin')
@login_required
def mood_checkin():
    realm_id = request.args.get('realm')
    if not realm_id:
        return redirect(url_for('home'))
    
    realm = Realm.query.get(realm_id)
    if not realm:
        return redirect(url_for('home'))
    
    return render_template('mood_checkin.html', realm=realm)

# Initialize database and seed data
def init_db():
    with app.app_context():
        db.create_all()
        
        # Check if realms already exist
        if Realm.query.count() == 0:
            seed_outcome_realms()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)