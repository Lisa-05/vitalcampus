# app.py
# Vital Campus - Main Flask Application

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
import uuid
import random

from database import (db, User, MoodEntry, Counsellor, Appointment, PeerPost,
                      PeerReply, Notification, StressForecast, Resource,
                      StudyBuddyProfile, Deadline)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vital-campus-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vitalcampus.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

    if Counsellor.query.count() == 0:
        counsellors = [
            Counsellor(full_name='Dr. Sarah Johnson', specialisation='Academic Stress', email='sarah.j@university.ac.za'),
            Counsellor(full_name='Mr. David Chen', specialisation='Time Management', email='david.c@university.ac.za'),
            Counsellor(full_name='Ms. Thandi Mokoena', specialisation='Depression & Anxiety', email='thandi.m@university.ac.za'),
            Counsellor(full_name='Dr. Robert Smith', specialisation='Relationships', email='robert.s@university.ac.za')
        ]
        for c in counsellors:
            db.session.add(c)
        db.session.commit()

    if not User.query.filter_by(email='admin@university.ac.za').first():
        admin = User(
            student_number='ADMIN001',
            preferred_name='System Admin',
            email='admin@university.ac.za',
            password=generate_password_hash('admin123'),
            faculty='Administration',
            year_of_study=0,
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()

    if not User.query.filter_by(email='student@university.ac.za').first():
        student = User(
            student_number='2025123456',
            preferred_name='Thimna',
            email='student@university.ac.za',
            password=generate_password_hash('student123'),
            faculty='ICT',
            year_of_study=3,
            role='student'
        )
        db.session.add(student)
        db.session.commit()

    if Resource.query.count() == 0:
        resources = [
            Resource(title='Breathe through the pressure',
                     description='A guided two-minute breathing reset for moments of overwhelm.',
                     category='Breathing', duration='2 min', icon='🌿', featured=True),
            Resource(title='Mindful study break',
                     description='A short meditation designed to restore focus between study sessions.',
                     category='Meditation', duration='6 min', icon='🧘'),
            Resource(title='A practical stress toolkit',
                     description='Small, evidence-based actions for managing a demanding week.',
                     category='Stress', duration='5 min read', icon='📖'),
            Resource(title='When deadlines pile up',
                     description='Learn how to prioritise academic work without burning out.',
                     category='Academic', duration='7 min read', icon='📚'),
            Resource(title='Sleep that supports learning',
                     description='Simple habits to improve sleep during the semester.',
                     category='Sleep', duration='4 min read', icon='😴'),
            Resource(title='Student money essentials',
                     description='A supportive guide to budgeting and financial wellbeing.',
                     category='Finance', duration='8 min read', icon='💰'),
        ]
        for r in resources:
            db.session.add(r)
        db.session.commit()


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password) and user.is_active:
            login_user(user)
            if user.last_login:
                flash(f'Welcome back, {user.preferred_name}!', 'success')
            else:
                flash(f'Welcome, {user.preferred_name}! 🌿 This is your first time using Vital Campus.', 'success')
            user.last_login = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        student_number = request.form.get('student_number')
        preferred_name = request.form.get('preferred_name')
        email = request.form.get('email')
        password = request.form.get('password')
        faculty = request.form.get('faculty')
        year_of_study = int(request.form.get('year_of_study'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'error')
            return redirect(url_for('login'))
        if User.query.filter_by(student_number=student_number).first():
            flash('Student number already registered.', 'error')
            return redirect(url_for('register'))

        user = User(
            student_number=student_number,
            preferred_name=preferred_name,
            email=email,
            password=generate_password_hash(password),
            faculty=faculty,
            year_of_study=year_of_study,
            role='student'
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    today = date.today()

    today_mood = MoodEntry.query.filter_by(user_id=current_user.id, log_date=today).first()

    week_moods = MoodEntry.query.filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.log_date >= today - timedelta(days=7)
    ).order_by(MoodEntry.log_date).all()

    upcoming_appointments = Appointment.query.filter(
        Appointment.student_id == current_user.id,
        Appointment.appointment_date >= today,
        Appointment.status.in_(['pending', 'confirmed'])
    ).order_by(Appointment.appointment_date).limit(3).all()

    low_mood_streak = 0
    check_date = today - timedelta(days=1)
    while check_date >= today - timedelta(days=30):
        mood = MoodEntry.query.filter_by(user_id=current_user.id, log_date=check_date).first()
        if mood and mood.mood_score <= 3:
            low_mood_streak += 1
        elif mood and mood.mood_score > 3:
            break
        else:
            break
        check_date -= timedelta(days=1)

    crisis_triggered = low_mood_streak >= 2

    wellness_score = None
    wellness_status = 'No data yet'

    if week_moods:
        avg_mood = sum(m.mood_score for m in week_moods) / len(week_moods)
        wellness_score = round(avg_mood * 10)
        if wellness_score >= 70:
            wellness_status = 'Doing Well 😊'
        elif wellness_score >= 50:
            wellness_status = 'Moderate 😐'
        else:
            wellness_status = 'Needs Attention 😔'
    else:
        wellness_score = None
        wellness_status = 'Log moods to see your score'

    current_hour = datetime.now().hour
    if current_hour < 12:
        greeting = 'Good morning'
    elif current_hour < 17:
        greeting = 'Good afternoon'
    else:
        greeting = 'Good evening'

    is_first_login = current_user.last_login is None

    return render_template('dashboard.html',
                         today_mood=today_mood,
                         week_moods=week_moods,
                         upcoming_appointments=upcoming_appointments,
                         low_mood_streak=low_mood_streak,
                         crisis_triggered=crisis_triggered,
                         wellness_score=wellness_score,
                         wellness_status=wellness_status,
                         is_first_login=is_first_login,
                         greeting=greeting)

@app.route('/mood', methods=['GET', 'POST'])
@login_required
def mood():
    if request.method == 'POST':
        rating = int(request.form.get('rating'))
        sleep_quality = request.form.get('sleep_quality')
        stress_triggers = request.form.get('stress_triggers')
        notes = request.form.get('notes', '')
        today = date.today()
        existing = MoodEntry.query.filter_by(user_id=current_user.id, log_date=today).first()
        if existing:
            existing.mood_score = rating
            existing.sleep_quality = sleep_quality
            existing.stress_triggers = stress_triggers
            existing.notes = notes
            flash('Mood updated successfully!', 'success')
        else:
            mood = MoodEntry(
                user_id=current_user.id,
                mood_score=rating,
                sleep_quality=sleep_quality,
                stress_triggers=stress_triggers,
                notes=notes,
                log_date=today
            )
            db.session.add(mood)
            flash('Mood logged successfully!', 'success')
        db.session.commit()

        low_streak = 0
        check_date = today - timedelta(days=1)
        while check_date >= today - timedelta(days=30):
            m = MoodEntry.query.filter_by(user_id=current_user.id, log_date=check_date).first()
            if m and m.mood_score <= 3:
                low_streak += 1
            else:
                break
            check_date -= timedelta(days=1)

        if low_streak >= 2 and rating <= 3:
            flash('⚠️ CRISIS ALERT: You have logged low mood for 3 consecutive days. Please seek support.', 'crisis')
            notification = Notification(
                user_id=current_user.id,
                type='crisis',
                message='Crisis alert: 3 consecutive low moods. Please reach out for support.',
                channel='app'
            )
            db.session.add(notification)
            db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('mood.html')

@app.route('/booking', methods=['GET', 'POST'])
@login_required
def booking():
    if request.method == 'POST':
        service_type = request.form.get('service_type')
        counsellor_id = request.form.get('counsellor_id')
        reason = request.form.get('reason', '')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')

        counsellor = Counsellor.query.get(counsellor_id) if counsellor_id else None
        if not counsellor:
            flash('Please select a counsellor.', 'error')
            return redirect(url_for('booking'))

        existing = Appointment.query.filter_by(
            counsellor_id=counsellor_id,
            appointment_date=datetime.strptime(appointment_date, '%Y-%m-%d').date(),
            appointment_time=appointment_time,
            status='confirmed'
        ).first()
        if existing:
            flash('This slot is already booked. Please select another time.', 'error')
            return redirect(url_for('booking'))

        appointment = Appointment(
            student_id=current_user.id,
            counsellor_id=counsellor_id,
            service_type=service_type,
            reason=reason,
            appointment_date=datetime.strptime(appointment_date, '%Y-%m-%d').date(),
            appointment_time=appointment_time,
            status='pending'
        )
        db.session.add(appointment)
        db.session.commit()

        notification = Notification(
            user_id=current_user.id,
            type='appointment',
            message=f'Appointment booked with {counsellor.full_name} on {appointment_date} at {appointment_time}',
            channel='app'
        )
        db.session.add(notification)
        db.session.commit()

        flash(f'Appointment booked successfully with {counsellor.full_name}!', 'success')
        return redirect(url_for('dashboard'))

    counsellors = Counsellor.query.filter_by(is_available=True).all()
    today = date.today()
    return render_template('booking.html', counsellors=counsellors, today=today)

@app.route('/forum', methods=['GET', 'POST'])
@login_required
def forum():
    if request.method == 'POST':
        category = request.form.get('category')
        content = request.form.get('content')
        animals = ['Panda', 'Fox', 'Koala', 'Lion', 'Tiger', 'Elephant', 'Dolphin', 'Eagle', 'Wolf', 'Bear']
        alias = f"{random.choice(animals)}{random.randint(10, 99)}"
        post = PeerPost(
            user_id=current_user.id,
            anonymous_alias=alias,
            content=content,
            category=category
        )
        db.session.add(post)
        db.session.commit()
        flash('Post published anonymously!', 'success')
        return redirect(url_for('forum'))
    posts = PeerPost.query.filter_by(is_flagged=False).order_by(PeerPost.posted_at.desc()).all()
    return render_template('forum.html', posts=posts)

@app.route('/forum/reply/<int:post_id>', methods=['POST'])
@login_required
def forum_reply(post_id):
    content = request.form.get('content')
    post = PeerPost.query.get(post_id)
    if not post:
        flash('Post not found.', 'error')
        return redirect(url_for('forum'))
    animals = ['Panda', 'Fox', 'Koala', 'Lion', 'Tiger', 'Elephant', 'Dolphin', 'Eagle', 'Wolf', 'Bear']
    alias = f"{random.choice(animals)}{random.randint(10, 99)}"
    reply = PeerReply(
        post_id=post_id,
        user_id=current_user.id,
        anonymous_alias=alias,
        content=content
    )
    db.session.add(reply)
    db.session.commit()
    flash('Reply posted anonymously!', 'success')
    return redirect(url_for('forum'))

@app.route('/workload', methods=['GET', 'POST'])
@login_required
def workload():
    today = date.today()

    if request.method == 'POST' and request.form.get('form_type') == 'deadline':
        course = request.form.get('course', '').strip()
        due_date_str = request.form.get('due_date')
        weighting = request.form.get('weighting', '20')

        if not course or not due_date_str:
            flash('Please fill in both course name and due date.', 'error')
        else:
            try:
                weighting_int = int(weighting) if weighting else 20
                due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                new_deadline = Deadline(
                    user_id=current_user.id,
                    course=course,
                    due_date=due_date_obj,
                    weighting=weighting_int
                )
                db.session.add(new_deadline)
                db.session.commit()
                flash(f'Deadline "{course}" added!', 'success')
            except ValueError:
                flash('Invalid date or weighting.', 'error')
        return redirect(url_for('workload'))

    forecast = StressForecast.query.filter_by(user_id=current_user.id)\
        .order_by(StressForecast.forecast_date.desc()).first()
    if not forecast:
        forecast = StressForecast(
            user_id=current_user.id,
            forecast_date=today + timedelta(days=7),
            stress_level='High',
            recommendation='Start exam prep 3 days early. Review your deadlines and create a study schedule.'
        )
        db.session.add(forecast)
        db.session.commit()

    deadlines = Deadline.query.filter_by(user_id=current_user.id, completed=False)\
        .order_by(Deadline.due_date.asc()).all()

    saved_plans = Notification.query.filter_by(user_id=current_user.id, type='study_plan')\
        .order_by(Notification.sent_at.desc()).all()

    return render_template('workload.html',
                         forecast=forecast,
                         deadlines=deadlines,
                         saved_plans=saved_plans)

@app.route('/workload/deadline/<int:deadline_id>/delete', methods=['POST'])
@login_required
def delete_deadline(deadline_id):
    deadline = Deadline.query.get_or_404(deadline_id)
    if deadline.user_id != current_user.id:
        flash('Not authorised.', 'error')
        return redirect(url_for('workload'))
    db.session.delete(deadline)
    db.session.commit()
    flash('Deadline removed.', 'info')
    return redirect(url_for('workload'))

@app.route('/workload/save-plan', methods=['POST'])
@login_required
def save_study_plan():
    plan_text = request.form.get('plan_text', '')
    module_name = request.form.get('module_name', 'Study Plan')
    if not plan_text:
        flash('No plan to save.', 'error')
        return redirect(url_for('workload'))
    note = Notification(
        user_id=current_user.id,
        type='study_plan',
        message=f'{module_name}: {plan_text}',
        channel='app'
    )
    db.session.add(note)
    db.session.commit()
    flash('Study plan saved to your workload page!', 'success')
    return redirect(url_for('workload'))

@app.route('/workload/saved-plan/<int:plan_id>/delete', methods=['POST'])
@login_required
def delete_saved_plan(plan_id):
    plan = Notification.query.get_or_404(plan_id)
    if plan.user_id != current_user.id:
        flash('Not authorised.', 'error')
        return redirect(url_for('workload'))
    db.session.delete(plan)
    db.session.commit()
    flash('Saved plan removed.', 'info')
    return redirect(url_for('workload'))

@app.route('/resources')
@login_required
def resources():
    all_resources = Resource.query.order_by(Resource.created_at.asc()).all()
    featured = next((r for r in all_resources if r.featured), None)
    return render_template('resources.html', resources=all_resources, featured=featured)

@app.route('/study-buddy', methods=['GET', 'POST'])
@login_required
def studybuddy():
    my_profile = StudyBuddyProfile.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        courses = request.form.getlist('courses')
        learning_style = request.form.get('learning_style', 'Visual')
        study_method = request.form.get('study_method', 'Either')
        bio = request.form.get('bio', '')
        if not courses:
            flash('Please select at least one course.', 'error')
            return redirect(url_for('studybuddy'))
        if my_profile:
            my_profile.courses = ','.join(courses)
            my_profile.learning_style = learning_style
            my_profile.study_method = study_method
            my_profile.bio = bio
            flash('Study buddy preferences updated!', 'success')
        else:
            my_profile = StudyBuddyProfile(
                user_id=current_user.id,
                courses=','.join(courses),
                learning_style=learning_style,
                study_method=study_method,
                bio=bio
            )
            db.session.add(my_profile)
            flash('Study buddy profile created!', 'success')
        db.session.commit()
        return redirect(url_for('studybuddy'))

    matches = []
    if my_profile:
        my_courses = set(my_profile.courses.split(','))
        all_profiles = StudyBuddyProfile.query.filter(StudyBuddyProfile.user_id != current_user.id).all()
        for p in all_profiles:
            other_courses = set(p.courses.split(','))
            shared = my_courses & other_courses
            if shared:
                score = len(shared)
                if p.learning_style == my_profile.learning_style:
                    score += 1
                if p.study_method == my_profile.study_method or p.study_method == 'Either' or my_profile.study_method == 'Either':
                    score += 1
                matches.append({'profile': p, 'score': score, 'shared': list(shared)})
        matches.sort(key=lambda m: m['score'], reverse=True)

    return render_template('studybuddy.html', my_profile=my_profile, matches=matches)

@app.route('/notifications')
@login_required
def notifications():
    user_notifications = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.type != 'study_plan'
    ).order_by(Notification.sent_at.desc()).all()
    return render_template('notifications.html', notifications=user_notifications)

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('dashboard'))

    total_users = User.query.count()
    total_moods = MoodEntry.query.count()
    total_appointments = Appointment.query.count()
    total_posts = PeerPost.query.count()
    total_counsellors = Counsellor.query.count()

    faculty_data = {}
    faculties = ['ICT', 'Engineering', 'Commerce', 'Education', 'Health Sciences', 'Humanities']
    for f in faculties:
        faculty_data[f] = User.query.filter_by(faculty=f).count()

    return render_template('admin.html',
                         total_users=total_users,
                         total_moods=total_moods,
                         total_appointments=total_appointments,
                         total_posts=total_posts,
                         total_counsellors=total_counsellors,
                         faculty_data=faculty_data)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)