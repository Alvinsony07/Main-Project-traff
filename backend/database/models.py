from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    full_name = Column(String(150), nullable=True)
    phone_number = Column(String(20), nullable=True)
    organization = Column(String(150), nullable=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), default='user')
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    failed_login_attempts = Column(Integer, default=0)
    is_locked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    reports = relationship("AccidentReport", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

class LaneStats(Base):
    __tablename__ = 'lane_stats'
    id = Column(Integer, primary_key=True, index=True)
    lane_id = Column(Integer, nullable=False)
    vehicle_count = Column(Integer, default=0)
    density = Column(String(20))
    timestamp = Column(DateTime, default=datetime.utcnow)

class VehicleLog(Base):
    __tablename__ = 'vehicle_logs'
    id = Column(Integer, primary_key=True, index=True)
    lane_id = Column(Integer, nullable=False)
    vehicle_type = Column(String(50), nullable=False)
    count = Column(Integer, default=1)
    timestamp = Column(DateTime, default=datetime.utcnow)

class AmbulanceEvent(Base):
    __tablename__ = 'ambulance_events'
    id = Column(Integer, primary_key=True, index=True)
    lane_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

class AccidentReport(Base):
    __tablename__ = 'accident_reports'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    location = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(String(20), default='Reported')
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="reports")
    dispatches = relationship("DispatchLog", back_populates="report")

class DispatchLog(Base):
    __tablename__ = 'dispatch_logs'
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey('accident_reports.id'), nullable=False)
    hospital_name = Column(String(255), nullable=False)
    hospital_lat = Column(Float, nullable=True)
    hospital_lng = Column(Float, nullable=True)
    accident_lat = Column(Float, nullable=True)
    accident_lng = Column(Float, nullable=True)
    distance_km = Column(Float, nullable=True)
    status = Column(String(20), default='Dispatched')
    timestamp = Column(DateTime, default=datetime.utcnow)
    report = relationship("AccidentReport", back_populates="dispatches")

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="audit_logs")

class SystemSetting(Base):
    __tablename__ = 'system_settings'
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
