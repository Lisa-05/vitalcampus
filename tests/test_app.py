# tests/test_app.py
import unittest
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from database import User, MoodEntry, Counsellor, Appointment, PeerPost

class VitalCampusTestCase(unittest.TestCase):
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        db.create_all()
        
        test_user = User(
            student_number='TEST001',
            preferred_name='Test User',
            email='test@university.ac.za',
            password='test123',
            faculty='ICT',
            year_of_study=3,
            role='student'
        )
        db.session.add(test_user)
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
    
    def test_user_creation(self):
        user = User.query.filter_by(email='test@university.ac.za').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.preferred_name, 'Test User')
    
    def test_login_success(self):
        response = self.app.post('/login', data={
            'email': 'test@university.ac.za',
            'password': 'test123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    def test_login_failure(self):
        response = self.app.post('/login', data={
            'email': 'wrong@email.com',
            'password': 'wrong'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email', response.data)
    
    def test_mood_logging(self):
        self.app.post('/login', data={
            'email': 'test@university.ac.za',
            'password': 'test123'
        })
        
        response = self.app.post('/mood', data={
            'rating': '7',
            'sleep_quality': 'Good',
            'stress_triggers': 'Assignments',
            'notes': 'Feeling good'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        mood = MoodEntry.query.first()
        self.assertIsNotNone(mood)
        self.assertEqual(mood.mood_score, 7)
    
    def test_booking_creation(self):
        self.app.post('/login', data={
            'email': 'test@university.ac.za',
            'password': 'test123'
        })
        
        counsellor = Counsellor(
            full_name='Dr. Test',
            specialisation='Test',
            email='test@counsellor.com'
        )
        db.session.add(counsellor)
        db.session.commit()
        
        response = self.app.post('/booking', data={
            'service_type': 'Personal Counselling',
            'counsellor_id': counsellor.id,
            'reason': 'Test booking',
            'appointment_date': str(date.today() + timedelta(days=7)),
            'appointment_time': '10:00 AM'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        appointment = Appointment.query.first()
        self.assertIsNotNone(appointment)
        self.assertEqual(appointment.service_type, 'Personal Counselling')
    
    def test_forum_post_creation(self):
        self.app.post('/login', data={
            'email': 'test@university.ac.za',
            'password': 'test123'
        })
        
        response = self.app.post('/forum', data={
            'category': 'Academics',
            'content': 'Test forum post'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        post = PeerPost.query.first()
        self.assertIsNotNone(post)
        self.assertEqual(post.content, 'Test forum post')
        self.assertNotEqual(post.anonymous_alias, 'Test User')

if __name__ == '__main__':
    unittest.main()