from flask import Flask, render_template, Response, jsonify, request, redirect, url_for, session, flash, make_response
from config import Config
from database.db import init_db, db
from database.models import User, LaneStats, VehicleLog, DispatchLog, AccidentReport
from models.signal_controller import SignalController
from utils.video_processor import VideoProcessor
from blueprints.user import user_bp
import threading
import time
import os

app = Flask(__name__)
app.config.from_object(Config)

init_db(app)
app.register_blueprint(user_bp)

# Initialize Core Components
signal_controller = SignalController(num_lanes=4)
app.config['SIGNAL_CONTROLLER'] = signal_controller
video_processor = VideoProcessor(Config, app)

# Global background timer thread for signal updates
def signal_timer_loop():
    while True:
        # Get density callback
        def get_all_counts():
            # Access latest count from video processor for all lanes
            return {i: video_processor.get_lane_count(i) for i in range(4)}

        # Pass callback and logic reference to controller
        signal_controller.update_state(time.time(), get_all_counts, video_processor.traffic_logic)
        time.sleep(1)

signal_thread = threading.Thread(target=signal_timer_loop, daemon=True)
signal_thread.start()

# --- Routes ---

@app.route('/')
def index():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return render_template('index.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        # Check if account is locked
        if user and user.is_locked:
            msg = 'Account locked due to too many failed attempts. Contact admin.'
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'success': False, 'message': msg})
            flash(msg)
            return render_template('login.html')
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session.permanent = True  # Enable session timeout
            db.session.commit()  # Persist reset of failed_login_attempts
            redirect_url = url_for('dashboard') if user.role == 'admin' else url_for('user.dashboard')
            
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'success': True, 'redirect': redirect_url})
            return redirect(redirect_url)
        
        # Persist failed login attempt counter
        if user:
            db.session.commit()
            
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'success': False, 'message': 'Invalid credentials'})
            
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if admin
    user = User.query.get(session['user_id'])
    
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('login'))

    if user.role != 'admin':
        return redirect(url_for('user.dashboard'))
        
    return render_template('dashboard.html')

@app.route('/analysis')
def analysis():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('analysis.html')

@app.route('/city_overview')
def city_overview():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('city_overview.html')

@app.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('settings.html')

@app.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('reports.html')

@app.route('/camera_config')
def camera_config():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('camera_config.html')

@app.route('/video_feed/<int:lane_id>')
def video_feed(lane_id):
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen_frames(lane_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_snapshot/<int:lane_id>')
def video_snapshot(lane_id):
    """Serve a single frame snapshot for JS polling (bypasses browser connection limits)"""
    frame_bytes = video_processor.get_frame(lane_id)
    if frame_bytes:
        return Response(frame_bytes, mimetype='image/jpeg')
    else:
        # Return a 1x1 transparent pixel or 404 if not ready
        return "Not Ready", 404

def gen_frames(lane_id):
    while True:
        frame_bytes = video_processor.get_frame(lane_id)
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            time.sleep(0.1)

@app.route('/api/status')
def get_status():
    """API for AJAX updates on the dashboard"""
    status = signal_controller.get_status()
    lane_data = video_processor.lane_data
    return jsonify({
        'signal_status': status,
        'lane_data': lane_data
    })

@app.route('/api/city_map_data')
def city_map_data():
    """Aggregated API for City Overview map — traffic + incidents + dispatches"""
    status = signal_controller.get_status()
    lane_data = video_processor.lane_data

    # Accident reports (recent, with GPS)
    reports = AccidentReport.query.order_by(AccidentReport.timestamp.desc()).limit(20).all()
    reports_data = [{
        'id': r.id,
        'location': r.location,
        'description': r.description,
        'latitude': r.latitude,
        'longitude': r.longitude,
        'status': r.status,
        'timestamp': r.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'user': r.user.username if r.user else 'Unknown'
    } for r in reports]

    # Active dispatches
    dispatches = DispatchLog.query.filter(
        DispatchLog.status.in_(['Dispatched', 'En Route', 'Arrived', 'Patient Loaded'])
    ).order_by(DispatchLog.timestamp.desc()).all()
    dispatch_data = [{
        'id': d.id,
        'hospital_name': d.hospital_name,
        'hospital_lat': d.hospital_lat,
        'hospital_lng': d.hospital_lng,
        'accident_lat': d.accident_lat,
        'accident_lng': d.accident_lng,
        'distance_km': d.distance_km,
        'status': d.status,
        'timestamp': d.timestamp.strftime('%H:%M:%S')
    } for d in dispatches]

    # Summary counts
    total_vehicles = sum(
        (lane_data.get(str(i), {}).get('count', 0) for i in range(4)), 0
    )
    active_incidents = AccidentReport.query.filter(AccidentReport.status != 'Resolved').count()

    return jsonify({
        'signal_status': status,
        'lane_data': lane_data,
        'reports': reports_data,
        'dispatches': dispatch_data,
        'summary': {
            'total_vehicles': total_vehicles,
            'active_incidents': active_incidents,
            'active_dispatches': len(dispatch_data)
        }
    })

@app.route('/api/stats')
def get_stats():
    """API for Advanced Analysis Charts"""
    from sqlalchemy import func, extract
    
    # 1. Traffic Volume Trend (Last 24 Hours)
    # Group by hour for a cleaner trend line if lots of data, or just last 50 entries
    trend_stats = LaneStats.query.order_by(LaneStats.timestamp.desc()).limit(50).all()
    trend_data = [{
        'time': s.timestamp.strftime('%H:%M:%S'),
        'count': s.vehicle_count,
        'lane': s.lane_id
    } for s in trend_stats]
    trend_data.reverse() # Oldest to newest
    
    # 2. Vehicle Distribution (Total Aggregated)
    dist_query = db.session.query(
        VehicleLog.vehicle_type, 
        func.sum(VehicleLog.count)
    ).group_by(VehicleLog.vehicle_type).all()
    dist_data = {type_: count for type_, count in dist_query}
    
    # 3. Peak Traffic Hours (Aggregated by Hour of Day)
    # Extracts hour from timestamp and sums traffic
    peak_query = db.session.query(
        extract('hour', LaneStats.timestamp).label('h'),
        func.sum(LaneStats.vehicle_count)
    ).group_by('h').all()
    # Fill missing hours with 0
    peak_data = {i: 0 for i in range(24)}
    for h, count in peak_query:
        peak_data[int(h)] = count
        
    # 4. Lane Load Performance (Avg Density per Lane)
    lane_query = db.session.query(
        LaneStats.lane_id,
        func.avg(LaneStats.vehicle_count)
    ).group_by(LaneStats.lane_id).all()
    lane_data = {l: round(c, 1) for l, c in lane_query}

    # 5. Emergency Events / Overrides (DispatchLogs usually align with these)
    ambulance_events = db.session.query(DispatchLog).count()

    return jsonify({
        'trend': trend_data,
        'distribution': dist_data,
        'peak_hours': peak_data,
        'lane_performance': lane_data,
        'ambulance_events': ambulance_events
    })

@app.route('/api/export_stats')
def export_stats():
    """Export all stats to CSV"""
    import io
    import csv
    
    # Query all stats
    stats = LaneStats.query.order_by(LaneStats.timestamp.desc()).all()
    
    # Create CSV in memory
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Lane ID', 'Vehicle Count', 'Density Label', 'Timestamp'])
    
    for s in stats:
        cw.writerow([s.id, s.lane_id, s.vehicle_count, s.density, s.timestamp])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=traffic_stats.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/setup_streams', methods=['POST'])
def setup_streams():
    """Helper to start the video processing with uploaded videos"""
    # Ensure uploads folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        
    final_sources = []
    
    for i in range(4):
        # 1. Check for Camera/URL input
        cam_key = f'cam_{i+1}'
        cam_input = request.form.get(cam_key, '').strip()
        
        # 2. Check for File Upload
        file_key = f'video_{i+1}'
        file_obj = request.files.get(file_key)
        
        # Logic: Prefer Camera input if provided, else File
        if cam_input:
            # Check if it's an integer index (webcam)
            if cam_input.isdigit():
                final_sources.append(int(cam_input))
            else:
                final_sources.append(cam_input)
        elif file_obj and file_obj.filename != '':
            # Save and use file
            path = os.path.join(app.config['UPLOAD_FOLDER'], file_obj.filename)
            file_obj.save(path)
            final_sources.append(path)
        else:
            final_sources.append(None)
            
    # Ensure exactly 4 items
    while len(final_sources) < 4:
        final_sources.append(None)
        
    print(f"Starting streams with sources: {final_sources}")
    video_processor.start_streams(final_sources)
    return redirect(url_for('dashboard'))

@app.route('/api/override', methods=['POST'])
def override_signal():
    """Manual override for traffic signal"""
    try:
        data = request.json
        lane_id = int(data.get('lane_id', 0))
        success = signal_controller.force_switch(lane_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/dispatch', methods=['POST'])
def dispatch_ambulance():
    """Record an ambulance dispatch to the database"""
    try:
        data = request.json
        dispatch = DispatchLog(
            report_id=int(data.get('report_id', 0)),
            hospital_name=data.get('hospital_name', 'Unknown'),
            hospital_lat=data.get('hospital_lat'),
            hospital_lng=data.get('hospital_lng'),
            accident_lat=data.get('accident_lat'),
            accident_lng=data.get('accident_lng'),
            distance_km=data.get('distance_km'),
            status='Dispatched'
        )
        db.session.add(dispatch)
        db.session.commit()
        return jsonify({'success': True, 'dispatch_id': dispatch.id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/dispatch/active')
def get_active_dispatches():
    """Get active dispatches for the ambulance driver portal"""
    dispatches = DispatchLog.query.filter(
        DispatchLog.status.in_(['Dispatched', 'En Route', 'Arrived', 'Patient Loaded'])
    ).order_by(DispatchLog.timestamp.desc()).all()
    return jsonify({
        'dispatches': [{
            'id': d.id,
            'report_id': d.report_id,
            'hospital_name': d.hospital_name,
            'hospital_lat': d.hospital_lat,
            'hospital_lng': d.hospital_lng,
            'accident_lat': d.accident_lat,
            'accident_lng': d.accident_lng,
            'distance_km': d.distance_km,
            'status': d.status,
            'timestamp': d.timestamp.strftime('%H:%M:%S'),
            'description': d.report.description if d.report else '',
            'location': d.report.location if d.report else ''
        } for d in dispatches]
    })

@app.route('/api/dispatch/<int:dispatch_id>/accept', methods=['POST'])
def accept_dispatch(dispatch_id):
    """Ambulance driver accepts a dispatch"""
    d = DispatchLog.query.get(dispatch_id)
    if d:
        d.status = 'En Route'
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/dispatch/<int:dispatch_id>/decline', methods=['POST'])
def decline_dispatch(dispatch_id):
    """Ambulance driver declines a dispatch"""
    d = DispatchLog.query.get(dispatch_id)
    if d:
        d.status = 'Declined'
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/dispatch/<int:dispatch_id>/status', methods=['POST'])
def update_dispatch_status(dispatch_id):
    """Update dispatch status to any valid step"""
    d = DispatchLog.query.get(dispatch_id)
    if d:
        new_status = request.json.get('status', '')
        valid = ['Dispatched', 'En Route', 'Arrived', 'Patient Loaded', 'Complete', 'Declined']
        if new_status in valid:
            d.status = new_status
            db.session.commit()
            return jsonify({'success': True, 'status': new_status})
    return jsonify({'success': False})

@app.route('/ambulance')
def ambulance_portal():
    """Ambulance Driver Portal - receives live dispatch alerts"""
    return render_template('ambulance.html')

@app.cli.command("create-admin")
def create_admin():
    """Creates a default admin user"""
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        if User.query.filter_by(username='admin').first():
            print("Admin user already exists.")
        else:
            u = User(username='admin', role='admin')
            u.set_password('admin123')
            db.session.add(u)
            db.session.commit()
            print("Admin user created (admin/admin123)")

@app.cli.command("unlock-user")
def unlock_user():
    """Unlock a locked user account"""
    import sys
    username = input("Username to unlock: ").strip()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            user.is_locked = False
            user.failed_login_attempts = 0
            db.session.commit()
            print(f"User '{username}' has been unlocked.")
        else:
            print(f"User '{username}' not found.")

if __name__ == '__main__':
    # Start the app
    # In a full deployment use gunicorn, for here app.run
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
