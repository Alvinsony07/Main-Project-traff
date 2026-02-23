from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database.models import User, AccidentReport
from database.db import db
from datetime import datetime

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('user.register'))
            
        new_user = User(username=username, role='user')
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
        
    return render_template('user/register.html')

@user_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
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
def report_accident():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    location = request.form.get('location')
    description = request.form.get('description')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    
    if location:
        report = AccidentReport(
            user_id=session['user_id'],
            location=location,
            description=description,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            status='Reported'
        )
        db.session.add(report)
        db.session.commit()
        flash('Accident reported successfully. Authorities have been notified.')
    else:
        flash('Location is required.')
        
    return redirect(url_for('user.dashboard'))

@user_bp.route('/api/reports')
def get_reports():
    # Return last 10 reports
    reports = AccidentReport.query.order_by(AccidentReport.timestamp.desc()).limit(10).all()
    return {
        'reports': [{
            'id': r.id,
            'location': r.location,
            'description': r.description,
            'latitude': r.latitude,
            'longitude': r.longitude,
            'timestamp': r.timestamp.strftime('%H:%M:%S'),
            'status': r.status,
            'user': r.user.username
        } for r in reports]
    }
