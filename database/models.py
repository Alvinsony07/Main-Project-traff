from datetime import datetime
from .db import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    role = db.Column(db.String(20), default='user') # 'admin' or 'user'

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
