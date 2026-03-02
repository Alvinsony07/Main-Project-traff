from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database.models import User, AccidentReport
from database.db import db
from datetime import datetime
from functools import wraps
import html

user_bp = Blueprint('user', __name__, url_prefix='/user')

def user_login_required(f):
    """Decorator to protect user-facing routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        full_name = request.form.get('full_name', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        organization = request.form.get('organization', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or len(username) < 3:
            flash('Username must be at least 3 characters')
            return redirect(url_for('user.register'))

        if not full_name:
            flash('Full Name is required')
            return redirect(url_for('user.register'))

        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('user.register'))
        
        # Validate password strength
        is_valid, msg = User.validate_password_strength(password)
        if not is_valid:
            flash(msg)
            return redirect(url_for('user.register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('user.register'))
            
        new_user = User(
            username=username, 
            full_name=full_name,
            phone_number=phone_number,
            organization=organization,
            role='user'
        )
        new_user.set_password(password)
        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Registration failed. Please try again.')
            return redirect(url_for('user.register'))
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
        
    return render_template('user/register.html')

@user_bp.route('/dashboard')
@user_login_required
def dashboard():
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('login'))

    if user.role != 'user':
        return redirect(url_for('dashboard')) # Redirect admins to main dashboard
        
    # Get user's reports
    my_reports = AccidentReport.query.filter_by(user_id=user.id).order_by(AccidentReport.timestamp.desc()).all()
    
    return render_template('user/dashboard.html', user=user, reports=my_reports)

@user_bp.route('/report_accident', methods=['POST'])
@user_login_required
def report_accident():
    location = request.form.get('location', '').strip()
    description = request.form.get('description', '').strip()
    latitude = request.form.get('latitude', '').strip()
    longitude = request.form.get('longitude', '').strip()
    
    if not location:
        flash('Location is required.')
        return redirect(url_for('user.dashboard'))
    
    # Validate lat/lng to prevent crash on invalid input
    try:
        lat_val = float(latitude) if latitude else None
    except (ValueError, TypeError):
        lat_val = None
    try:
        lng_val = float(longitude) if longitude else None
    except (ValueError, TypeError):
        lng_val = None
    
    report = AccidentReport(
        user_id=session['user_id'],
        location=location,
        description=description,
        latitude=lat_val,
        longitude=lng_val,
        status='Reported'
    )
    try:
        db.session.add(report)
        db.session.commit()
        flash('Accident reported successfully. Authorities have been notified.')
    except Exception:
        db.session.rollback()
        flash('Failed to submit report. Please try again.')
        
    return redirect(url_for('user.dashboard'))

@user_bp.route('/api/reports')
@user_login_required
def get_reports():
    """Return last 10 reports — sanitized for XSS prevention."""
    reports = AccidentReport.query.order_by(AccidentReport.timestamp.desc()).limit(10).all()
    return jsonify({
        'reports': [{
            'id': r.id,
            'location': html.escape(r.location or ''),
            'description': html.escape(r.description or ''),
            'latitude': r.latitude,
            'longitude': r.longitude,
            'timestamp': r.timestamp.strftime('%H:%M:%S'),
            'status': r.status,
            'user': html.escape(r.user.username) if r.user else 'Unknown'
        } for r in reports]
    })
