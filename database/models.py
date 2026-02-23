from datetime import datetime
from .db import db
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import os

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    organization = db.Column(db.String(150), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'
    password_changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    failed_login_attempts = db.Column(db.Integer, default=0)
    is_locked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """Hash password using scrypt (strongest werkzeug method)"""
        self.password_hash = generate_password_hash(password, method='scrypt', salt_length=16)
        self.password_changed_at = datetime.utcnow()

    def check_password(self, password):
        """Verify password against stored hash"""
        if self.is_locked:
            return False
        result = check_password_hash(self.password_hash, password)
        if result:
            self.failed_login_attempts = 0
        else:
            self.failed_login_attempts = (self.failed_login_attempts or 0) + 1
            if self.failed_login_attempts >= 5:
                self.is_locked = True
        return result

    @staticmethod
    def validate_password_strength(password):
        """Enforce minimum password requirements"""
        if len(password) < 6:
            return False, 'Password must be at least 6 characters'
        return True, 'OK'

class LaneStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lane_id = db.Column(db.Integer, nullable=False) # 1, 2, 3, 4
    vehicle_count = db.Column(db.Integer, default=0)
    density = db.Column(db.String(20)) # "Low", "Medium", "High"
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class VehicleLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lane_id = db.Column(db.Integer, nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)
    count = db.Column(db.Integer, default=1)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class AmbulanceEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lane_id = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

class AccidentReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='Reported') # Reported, Verified, Resolved
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('reports', lazy=True))

class DispatchLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('accident_report.id'), nullable=False)
    hospital_name = db.Column(db.String(255), nullable=False)
    hospital_lat = db.Column(db.Float, nullable=True)
    hospital_lng = db.Column(db.Float, nullable=True)
    accident_lat = db.Column(db.Float, nullable=True)
    accident_lng = db.Column(db.Float, nullable=True)
    distance_km = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default='Dispatched')  # Dispatched, En Route, Arrived
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    report = db.relationship('AccidentReport', backref=db.backref('dispatches', lazy=True))
