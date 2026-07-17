

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
import uuid

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    student_number = db.Column(db.String(15), unique=True, nullable=False)
    preferred_name = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    faculty = db.Column(db.String(80), nullable=False)
    year_of_study = db.Column(db.SmallInteger, nullable=False)
    role = db.Column(db.String(20), default='student')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    moods = db.relationship('MoodEntry', backref='user', lazy=True)
    appointments = db.relationship('Appointment', backref='user', lazy=True)
    posts = db.relationship('PeerPost', backref='user', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.preferred_name}>'


class MoodEntry(db.Model):
    __tablename__ = 'mood_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mood_score = db.Column(db.SmallInteger, nullable=False)
    sleep_quality = db.Column(db.String(10), nullable=False)
    stress_triggers = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.String(120), nullable=True)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)
    log_date = db.Column(db.Date, default=date.today)
    
    def __repr__(self):
        return f'<MoodEntry {self.mood_score}/10 - {self.log_date}>'


class Counsellor(db.Model):
    __tablename__ = 'counsellors'
    
    id = db.Column(db.Integer, primary_key=True)
    counsellor_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    full_name = db.Column(db.String(120), nullable=False)
    specialisation = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    appointments = db.relationship('Appointment', backref='counsellor', lazy=True)
    
    def __repr__(self):
        return f'<Counsellor {self.full_name}>'


class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    counsellor_id = db.Column(db.Integer, db.ForeignKey('counsellors.id'), nullable=False)
    service_type = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.String(200), nullable=True)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(15), default='pending')
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Appointment {self.service_type} - {self.status}>'


class PeerPost(db.Model):
    __tablename__ = 'peer_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    anonymous_alias = db.Column(db.String(40), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    is_flagged = db.Column(db.Boolean, default=False)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    replies = db.relationship('PeerReply', backref='post', lazy=True)
    
    def __repr__(self):
        return f'<PeerPost by {self.anonymous_alias}>'


class PeerReply(db.Model):
    __tablename__ = 'peer_replies'
    
    id = db.Column(db.Integer, primary_key=True)
    reply_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    post_id = db.Column(db.Integer, db.ForeignKey('peer_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    anonymous_alias = db.Column(db.String(40), nullable=False)
    content = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PeerReply to {self.post_id}>'


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    message = db.Column(db.String(300), nullable=False)
    channel = db.Column(db.String(10), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.type}>'


class StressForecast(db.Model):
    __tablename__ = 'stress_forecasts'
    
    id = db.Column(db.Integer, primary_key=True)
    forecast_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    forecast_date = db.Column(db.Date, nullable=False)
    stress_level = db.Column(db.String(20), nullable=False)
    recommendation = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)