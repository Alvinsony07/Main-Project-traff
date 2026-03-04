from flask import Flask, render_template, Response, jsonify, request, redirect, url_for, session, flash, make_response
from config import Config
from database.db import init_db, db
from database.models import User, LaneStats, VehicleLog, DispatchLog, AccidentReport, AuditLog
from models.signal_controller import SignalController
from utils.video_processor import VideoProcessor
from blueprints.user import user_bp
from werkzeug.utils import secure_filename
from functools import wraps
from collections import defaultdict
import threading
import time
import json
import os

# --- Rate Limiter (in-memory) ---
_login_attempts = defaultdict(list)  # IP -> list of timestamps
LOGIN_RATE_LIMIT = 5       # Max attempts
LOGIN_RATE_WINDOW = 300    # Per 5-minute window (seconds)

def _is_rate_limited(ip):
    """Check if an IP has exceeded login rate limit."""
    now = time.time()
    _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < LOGIN_RATE_WINDOW]
    return len(_login_attempts[ip]) >= LOGIN_RATE_LIMIT

def _record_attempt(ip):
    """Record a login attempt for rate limiting."""
    _login_attempts[ip].append(time.time())

# --- Auth Decorator ---
def login_required(f):
    """Decorator to protect routes that require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.headers.get('Accept') == 'application/json' or request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to protect routes that require admin privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.headers.get('Accept') == 'application/json' or request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            if request.headers.get('Accept') == 'application/json' or request.is_json:
                return jsonify({'error': 'Admin access required'}), 403
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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
        client_ip = request.remote_addr
        
        # Rate limiting check
        if _is_rate_limited(client_ip):
            msg = 'Too many login attempts. Please try again in 5 minutes.'
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'success': False, 'message': msg}), 429
            flash(msg)
            return render_template('login.html')
        
        _record_attempt(client_ip)
        
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
            # Clear rate limit on success
            _login_attempts.pop(client_ip, None)
            # Audit log
            AuditLog.log(
                action='login_success',
                details=f'User {username} logged in',
                user_id=user.id,
                ip_address=client_ip
            )
            redirect_url = url_for('dashboard') if user.role == 'admin' else url_for('user.dashboard')
            
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'success': True, 'redirect': redirect_url})
            return redirect(redirect_url)
        
        # Persist failed login attempt counter
        if user:
            db.session.commit()
        
        # Audit log for failed attempts
        AuditLog.log(
            action='login_failed',
            details=f'Failed login attempt for user: {username}',
            ip_address=client_ip
        )
            
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'success': False, 'message': 'Invalid credentials'})
            
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
@admin_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/analysis')
@login_required
def analysis():
    return render_template('analysis.html')

@app.route('/city_overview')
@login_required
def city_overview():
    return render_template('city_overview.html')

@app.route('/settings')
@admin_required
def settings():
    return render_template('settings.html')

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/camera_config')
@admin_required
def camera_config():
    return render_template('camera_config.html')

@app.route('/video_feed/<int:lane_id>')
@login_required
def video_feed(lane_id):
    """Video streaming route. Put this in the src attribute of an img tag."""
    if lane_id < 0 or lane_id > 3:
        return "Invalid lane", 400
    return Response(gen_frames(lane_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_snapshot/<int:lane_id>')
@login_required
def video_snapshot(lane_id):
    """Serve a single frame snapshot for JS polling (bypasses browser connection limits)"""
    if lane_id < 0 or lane_id > 3:
        return "Invalid lane", 400
    frame_bytes = video_processor.get_frame(lane_id)
    if frame_bytes:
        return Response(frame_bytes, mimetype='image/jpeg')
    else:
        # Return a 1x1 transparent pixel or 404 if not ready
        return "Not Ready", 404

def gen_frames(lane_id):
    """Generator for MJPEG stream. Yields frames until processor stops."""
    idle_count = 0
    while video_processor.running:
        frame_bytes = video_processor.get_frame(lane_id)
        if frame_bytes:
            idle_count = 0
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            idle_count += 1
            if idle_count > 300:  # 30 seconds of no frames = stop generator
                break
            time.sleep(0.1)

@app.route('/api/status')
@login_required
def get_status():
    """API for AJAX updates on the dashboard"""
    status = signal_controller.get_status()
    lane_data = video_processor.lane_data
    return jsonify({
        'signal_status': status,
        'lane_data': lane_data
    })

@app.route('/api/city_map_data')
@login_required
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
@login_required
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

@app.route('/api/reports_data')
@login_required
def reports_data():
    """Paginated, filterable API for Reports page"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    lane_filter = request.args.get('lane', None, type=int)  # 0-3
    density_filter = request.args.get('density', None, type=str)  # Low, Medium, High
    date_filter = request.args.get('date', None, type=str)  # YYYY-MM-DD
    
    per_page = min(per_page, 100)  # Cap at 100
    
    query = LaneStats.query
    
    if lane_filter is not None and 1 <= lane_filter <= 4:
        query = query.filter(LaneStats.lane_id == lane_filter)
    if density_filter and density_filter in ('Low', 'Medium', 'High'):
        query = query.filter(LaneStats.density == density_filter)
    if date_filter:
        try:
            from datetime import datetime as dt
            target = dt.strptime(date_filter, '%Y-%m-%d')
            from sqlalchemy import func
            query = query.filter(func.date(LaneStats.timestamp) == target.date())
        except ValueError:
            pass  # Invalid date format, skip filter
    
    query = query.order_by(LaneStats.timestamp.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    records = [{
        'id': s.id,
        'lane_id': s.lane_id,
        'vehicle_count': s.vehicle_count,
        'density': s.density or ('High' if s.vehicle_count > 20 else ('Medium' if s.vehicle_count > 10 else 'Low')),
        'timestamp': s.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for s in pagination.items]
    
    return jsonify({
        'records': records,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })

@app.route('/api/export_stats')
@admin_required
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

# --- Settings Persistence ---
SETTINGS_FILE = os.path.join(Config.BASE_DIR, 'system_settings.json')

def _load_settings():
    """Load settings from JSON file, return defaults if not found."""
    defaults = {
        'yolo_model': 'yolov8s',
        'confidence_threshold': 45,
        'ambulance_confidence': 65,
        'low_density_green': 15,
        'medium_density_green': 30,
        'high_density_green': 45,
        'dark_mode': True,
        'voice_alerts': True,
        'auto_dispatch': True,
        'data_retention': '30_days'
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                saved = json.load(f)
            defaults.update(saved)
        except (json.JSONDecodeError, IOError):
            pass
    return defaults

def _save_settings(data):
    """Save settings to JSON file."""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/api/settings', methods=['GET'])
@admin_required
def get_settings():
    """Get current system settings."""
    return jsonify(_load_settings())

@app.route('/api/settings', methods=['POST'])
@admin_required
def save_settings():
    """Save system settings."""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        current = _load_settings()
        # Whitelist valid settings keys
        allowed_keys = {
            'yolo_model', 'confidence_threshold', 'ambulance_confidence',
            'low_density_green', 'medium_density_green', 'high_density_green',
            'dark_mode', 'voice_alerts', 'auto_dispatch', 'data_retention'
        }
        for key in allowed_keys:
            if key in data:
                current[key] = data[key]
        
        _save_settings(current)
        # Audit log
        changed_keys = [k for k in allowed_keys if k in data]
        AuditLog.log(
            action='settings_changed',
            details=f'Updated: {", ".join(changed_keys)}',
            user_id=session.get('user_id'),
            ip_address=request.remote_addr
        )
        return jsonify({'success': True, 'settings': current})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate_pdf')
@admin_required
def generate_pdf():
    """Generate a PDF report of traffic statistics."""
    import io
    from datetime import datetime as dt
    
    # Gather data
    stats = LaneStats.query.order_by(LaneStats.timestamp.desc()).limit(100).all()
    dispatches = DispatchLog.query.order_by(DispatchLog.timestamp.desc()).limit(20).all()
    incidents = AccidentReport.query.order_by(AccidentReport.timestamp.desc()).limit(20).all()
    
    total_vehicles = sum(s.vehicle_count for s in stats)
    total_dispatches = DispatchLog.query.count()
    total_incidents = AccidentReport.query.count()
    
    # Build HTML content for PDF
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; color: #1a1a2e; }}
            h1 {{ color: #3b82f6; border-bottom: 3px solid #3b82f6; padding-bottom: 10px; }}
            h2 {{ color: #1e293b; margin-top: 30px; }}
            .meta {{ color: #64748b; font-size: 14px; margin-bottom: 30px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 13px; }}
            th {{ background: #3b82f6; color: white; padding: 10px; text-align: left; }}
            td {{ padding: 8px 10px; border-bottom: 1px solid #e2e8f0; }}
            tr:nth-child(even) {{ background: #f8fafc; }}
            .stat-box {{ display: inline-block; background: #f1f5f9; border-radius: 10px; padding: 15px 25px; margin: 5px; text-align: center; }}
            .stat-val {{ font-size: 28px; font-weight: bold; color: #3b82f6; }}
            .stat-lbl {{ font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 1px; }}
            .footer {{ margin-top: 40px; padding-top: 15px; border-top: 1px solid #e2e8f0; color: #94a3b8; font-size: 12px; }}
        </style>
    </head>
    <body>
        <h1>Traffic Vision AI — Analytics Report</h1>
        <div class="meta">Generated: {dt.now().strftime('%Y-%m-%d %H:%M:%S')} | System v3.0</div>
        
        <div>
            <div class="stat-box"><div class="stat-val">{total_vehicles}</div><div class="stat-lbl">Total Vehicles</div></div>
            <div class="stat-box"><div class="stat-val">{total_dispatches}</div><div class="stat-lbl">Dispatches</div></div>
            <div class="stat-box"><div class="stat-val">{total_incidents}</div><div class="stat-lbl">Incidents</div></div>
            <div class="stat-box"><div class="stat-val">{len(stats)}</div><div class="stat-lbl">Data Points</div></div>
        </div>
        
        <h2>Recent Traffic Records</h2>
        <table>
            <tr><th>ID</th><th>Lane</th><th>Vehicles</th><th>Density</th><th>Timestamp</th></tr>
    """
    
    for s in stats[:50]:
        density = s.density or ('High' if s.vehicle_count > 20 else ('Medium' if s.vehicle_count > 10 else 'Low'))
        html_content += f"<tr><td>#{s.id}</td><td>Lane {s.lane_id}</td><td>{s.vehicle_count}</td><td>{density}</td><td>{s.timestamp.strftime('%Y-%m-%d %H:%M')}</td></tr>\n"
    
    html_content += """</table>
        <h2>Recent Incident Reports</h2>
        <table>
            <tr><th>ID</th><th>Location</th><th>Status</th><th>Reported</th></tr>
    """
    
    for inc in incidents:
        html_content += f"<tr><td>#{inc.id}</td><td>{inc.location}</td><td>{inc.status}</td><td>{inc.timestamp.strftime('%Y-%m-%d %H:%M')}</td></tr>\n"
    
    html_content += f"""
        </table>
        <div class="footer">
            Traffic Vision AI — Autonomous Traffic Management System<br>
            This report was auto-generated. Data reflects records up to {dt.now().strftime('%Y-%m-%d %H:%M')}.
        </div>
    </body>
    </html>
    """
    
    response = make_response(html_content)
    response.headers['Content-Type'] = 'text/html'
    response.headers['Content-Disposition'] = f'attachment; filename=traffic_report_{dt.now().strftime("%Y%m%d_%H%M%S")}.html'
    return response

@app.route('/setup_streams', methods=['POST'])
@admin_required
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
            safe_name = secure_filename(file_obj.filename)
            if not safe_name:
                final_sources.append(None)
                continue
            # Validate file extension
            ext = safe_name.rsplit('.', 1)[-1].lower() if '.' in safe_name else ''
            if ext not in app.config.get('ALLOWED_VIDEO_EXTENSIONS', {'mp4', 'avi', 'mov', 'mkv', 'webm'}):
                print(f"Rejected upload: invalid extension '.{ext}'")
                final_sources.append(None)
                continue
            path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
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
@admin_required
def override_signal():
    """Manual override for traffic signal"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        lane_id = int(data.get('lane_id', -1))
        if lane_id < 0 or lane_id > 3:
            return jsonify({'success': False, 'error': 'Invalid lane_id. Must be 0-3.'}), 400
        success = signal_controller.force_switch(lane_id)
        # Audit log
        AuditLog.log(
            action='signal_override',
            details=f'Manual override to Lane {lane_id}',
            user_id=session.get('user_id'),
            ip_address=request.remote_addr
        )
        return jsonify({'success': success})
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'error': 'Invalid lane_id format'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/dispatch', methods=['POST'])
@login_required
def dispatch_ambulance():
    """Record an ambulance dispatch to the database"""
    try:
        data = request.json
        report_id = int(data.get('report_id', 0))
        
        # Validate that the report exists
        report = AccidentReport.query.get(report_id)
        if not report:
            return jsonify({'success': False, 'error': 'Invalid report ID'}), 400
        
        dispatch = DispatchLog(
            report_id=report_id,
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
        # Audit log
        AuditLog.log(
            action='dispatch_created',
            details=f'Dispatched to {data.get("hospital_name", "Unknown")} for report #{report_id}',
            user_id=session.get('user_id'),
            ip_address=request.remote_addr
        )
        return jsonify({'success': True, 'dispatch_id': dispatch.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/dispatch/active')
@login_required
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
@login_required
def accept_dispatch(dispatch_id):
    """Ambulance driver accepts a dispatch"""
    try:
        d = DispatchLog.query.get(dispatch_id)
        if d:
            d.status = 'En Route'
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Dispatch not found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/dispatch/<int:dispatch_id>/decline', methods=['POST'])
@login_required
def decline_dispatch(dispatch_id):
    """Ambulance driver declines a dispatch"""
    try:
        d = DispatchLog.query.get(dispatch_id)
        if d:
            d.status = 'Declined'
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Dispatch not found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/dispatch/<int:dispatch_id>/status', methods=['POST'])
@login_required
def update_dispatch_status(dispatch_id):
    """Update dispatch status to any valid step"""
    try:
        d = DispatchLog.query.get(dispatch_id)
        if d:
            new_status = request.json.get('status', '') if request.json else ''
            valid = ['Dispatched', 'En Route', 'Arrived', 'Patient Loaded', 'Complete', 'Declined']
            if new_status in valid:
                d.status = new_status
                db.session.commit()
                return jsonify({'success': True, 'status': new_status})
            return jsonify({'success': False, 'error': 'Invalid status value'}), 400
        return jsonify({'success': False, 'error': 'Dispatch not found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/ambulance')
@login_required
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

# --- Data Purge API ---
@app.route('/api/purge_data', methods=['POST'])
@admin_required
def purge_data():
    """Purge all historical traffic data (LaneStats, VehicleLog)."""
    try:
        lane_count = LaneStats.query.count()
        vehicle_count = VehicleLog.query.count()
        
        LaneStats.query.delete()
        VehicleLog.query.delete()
        db.session.commit()
        
        AuditLog.log(
            action='data_purge',
            details=f'Purged {lane_count} lane stats, {vehicle_count} vehicle logs',
            user_id=session.get('user_id'),
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'success': True,
            'purged': {'lane_stats': lane_count, 'vehicle_logs': vehicle_count}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# --- Error Handlers ---
@app.errorhandler(404)
def not_found_error(error):
    if request.headers.get('Accept') == 'application/json' or request.is_json:
        return jsonify({'error': 'Not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if request.headers.get('Accept') == 'application/json' or request.is_json:
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('404.html', error_code=500, error_msg='Internal Server Error'), 500

# --- Audit Trail API ---
@app.route('/api/audit_trail')
@admin_required
def audit_trail():
    """Returns recent audit log entries."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = min(per_page, 100)
    
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        'entries': [{
            'id': l.id,
            'action': l.action,
            'details': l.details,
            'user': l.user.username if l.user else 'System',
            'ip': l.ip_address,
            'timestamp': l.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        } for l in logs.items],
        'total': logs.total,
        'pages': logs.pages,
        'current_page': page
    })

# --- AI Congestion Prediction API ---
@app.route('/api/predictions')
@login_required
def get_predictions():
    """Predict traffic congestion for the next 6 hours based on historical patterns.
    Uses time-of-day weighted averages from stored LaneStats data.
    """
    from datetime import datetime as dt, timedelta
    from sqlalchemy import func, extract
    
    now = dt.now()
    predictions = []
    
    for offset in range(1, 7):  # Next 6 hours
        target_hour = (now.hour + offset) % 24
        
        # Query historical average for this hour across all days
        avg_result = db.session.query(
            func.avg(LaneStats.vehicle_count)
        ).filter(
            extract('hour', LaneStats.timestamp) == target_hour
        ).scalar()
        
        avg_count = round(float(avg_result or 0), 1)
        
        # Determine congestion level
        if avg_count > 25:
            level = 'High'
            color = '#ef4444'
        elif avg_count > 12:
            level = 'Medium'
            color = '#f59e0b'
        else:
            level = 'Low'
            color = '#10b981'
        
        predictions.append({
            'hour': f"{target_hour:02d}:00",
            'label': (now + timedelta(hours=offset)).strftime('%I %p'),
            'avg_vehicles': avg_count,
            'level': level,
            'color': color,
            'confidence': min(95, 60 + int(avg_count * 0.8))  # Simulated confidence
        })
    
    # Overall summary
    peak_hour = max(predictions, key=lambda x: x['avg_vehicles'])
    
    return jsonify({
        'predictions': predictions,
        'peak_prediction': peak_hour,
        'model': 'Historical Time-Series Average',
        'generated_at': now.strftime('%H:%M:%S')
    })

if __name__ == '__main__':
    # Start the app
    # In a full deployment use gunicorn, for here app.run
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
