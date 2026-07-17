# tests/test_app.py
import unittest
import sys
import os
from datetime import date, timedelta

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from database import User, MoodEntry, Counsellor, Appointment, PeerPost
from werkzeug.security import generate_password_hash

class VitalCampusTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment - runs before each test"""
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['LOGIN_DISABLED'] = False
        
        # Create application context
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create tables
        db.create_all()
        
        # Create test client
        self.client = app.test_client()
        
        # Create test user with hashed password
        test_user = User(
            student_number='TEST001',
            preferred_name='Test User',
            email='test@university.ac.za',
            password=generate_password_hash('test123'),
            faculty='ICT',
            year_of_study=3,
            role='student'
        )
        db.session.add(test_user)
        db.session.commit()
        
        # Store user ID for later use
        self.test_user_id = test_user.id
    
    def tearDown(self):
        """Clean up after tests - runs after each test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login(self, email='test@university.ac.za', password='test123'):
        """Helper method to log in a user"""
        return self.client.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)
    
    def test_user_creation(self):
        """Test that user can be created"""
        user = User.query.filter_by(email='test@university.ac.za').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.preferred_name, 'Test User')
        self.assertEqual(user.faculty, 'ICT')
        self.assertEqual(user.year_of_study, 3)
    
    def test_login_page_loads(self):
        """Test that login page loads"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Vital Campus', response.data)
    
    def test_login_success(self):
        """Test successful login"""
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back', response.data)
    
    def test_login_failure(self):
        """Test login with invalid credentials"""
        response = self.client.post('/login', data={
            'email': 'wrong@email.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        self.assertIn(b'Invalid email or password', response.data)
    
    def test_register_and_login(self):
        """Test registration then login flow"""
        # Register a new user
        response = self.client.post('/register', data={
            'student_number': '2025123456',
            'preferred_name': 'Thimna',
            'email': 'thimna@test.com',
            'password': 'password123',
            'faculty': 'ICT',
            'year_of_study': '3'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Login with the new user
        response = self.client.post('/login', data={
            'email': 'thimna@test.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back', response.data)
    
    def test_mood_logging(self):
        """Test that mood can be logged"""
        # Login first
        self.login()
        
        # Log a mood
        response = self.client.post('/mood', data={
            'rating': '7',
            'sleep_quality': 'Good',
            'stress_triggers': 'Assignments',
            'notes': 'Feeling good today'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify mood was saved
        mood = MoodEntry.query.filter_by(user_id=self.test_user_id).first()
        self.assertIsNotNone(mood)
        self.assertEqual(mood.mood_score, 7)
        self.assertEqual(mood.sleep_quality, 'Good')
        self.assertEqual(mood.notes, 'Feeling good today')
    
    def test_booking_creation(self):
        """Test that appointment can be booked"""
        # Login first
        self.login()
        
        # Create a counsellor
        counsellor = Counsellor(
            full_name='Dr. Test',
            specialisation='Test Specialisation',
            email='test@counsellor.com',
            is_available=True
        )
        db.session.add(counsellor)
        db.session.commit()
        
        # Book appointment
        response = self.client.post('/booking', data={
            'service_type': 'Personal Counselling',
            'counsellor_id': counsellor.id,
            'reason': 'Test booking',
            'appointment_date': str(date.today() + timedelta(days=7)),
            'appointment_time': '10:00 AM'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify appointment was saved
        appointment = Appointment.query.filter_by(student_id=self.test_user_id).first()
        self.assertIsNotNone(appointment)
        self.assertEqual(appointment.service_type, 'Personal Counselling')
        self.assertEqual(appointment.status, 'pending')
    
    def test_forum_post_creation(self):
        """Test that forum post can be created"""
        # Login first
        self.login()
        
        # Create forum post
        response = self.client.post('/forum', data={
            'category': 'Academics',
            'content': 'Test forum post message'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify post was saved
        post = PeerPost.query.filter_by(user_id=self.test_user_id).first()
        self.assertIsNotNone(post)
        self.assertEqual(post.content, 'Test forum post message')
        self.assertEqual(post.category, 'Academics')
        # Anonymous alias should NOT be the user's real name
        self.assertNotEqual(post.anonymous_alias, 'Test User')
    
    def test_dashboard_requires_login(self):
        """Test that dashboard redirects to login if not authenticated"""
        response = self.client.get('/dashboard', follow_redirects=True)
        self.assertIn(b'Please log in', response.data)
    
    def test_admin_access_denied_for_student(self):
        """Test that non-admin users cannot access admin page"""
        self.login()
        response = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b'You do not have permission', response.data)

if __name__ == '__main__':
    unittest.main()