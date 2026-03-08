import time
import json
import os
import io
import csv
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from backend.database.database import get_db
from backend.database.models import (
    User, LaneStats, VehicleLog, AmbulanceEvent,
    AccidentReport, DispatchLog, AuditLog, SystemSetting
)
from backend.config import settings

router = APIRouter()

# ========================
# AUTH (JWT-based)
# ========================
from passlib.context import CryptContext
from jose import JWTError, jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# In-memory rate limiter
_login_attempts = defaultdict(list)
LOGIN_RATE_LIMIT = 5
LOGIN_RATE_WINDOW = 300

def _is_rate_limited(ip: str) -> bool:
    now = time.time()
    _login_attempts[ip] = [t for t in _login_attempts[ip] if now - t < LOGIN_RATE_WINDOW]
    return len(_login_attempts[ip]) >= LOGIN_RATE_LIMIT

def _record_attempt(ip: str):
    _login_attempts[ip].append(time.time())

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


@router.post("/auth/login")
async def login(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    username = body.get("username", "")
    password = body.get("password", "")
    client_ip = request.client.host if request.client else "unknown"

    if _is_rate_limited(client_ip):
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again in 5 minutes.")

    _record_attempt(client_ip)

    user = db.query(User).filter(User.username == username).first()

    if user and user.is_locked:
        raise HTTPException(status_code=403, detail="Account locked. Contact admin.")

    if user and pwd_context.verify(password, user.password_hash):
        user.failed_login_attempts = 0
        db.commit()
        _login_attempts.pop(client_ip, None)

        token = create_access_token({"sub": str(user.id), "role": user.role, "username": user.username})

        # Audit
        audit = AuditLog(action="login_success", details=f"User {username} logged in", user_id=user.id, ip_address=client_ip)
        db.add(audit)
        db.commit()

        return {"success": True, "token": token, "role": user.role, "username": user.username}

    if user:
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
        db.commit()

    audit = AuditLog(action="login_failed", details=f"Failed login for: {username}", ip_address=client_ip)
    db.add(audit)
    db.commit()

    raise HTTPException(status_code=401, detail="Invalid credentials")


# ========================
# VIDEO STREAMING
# ========================
def gen_frames(lane_id: int):
    from backend.main import video_processor
    idle_count = 0
    while video_processor.running:
        frame = video_processor.get_frame(lane_id)
        if frame:
            idle_count = 0
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            idle_count += 1
            if idle_count > 300:
                break
            time.sleep(0.1)

@router.get("/video_feed/{lane_id}")
def video_feed(lane_id: int):
    from backend.main import video_processor
    if not video_processor or not video_processor.running:
        raise HTTPException(status_code=404, detail="Video stream offline")
    return StreamingResponse(gen_frames(lane_id), media_type="multipart/x-mixed-replace; boundary=frame")

@router.get("/video_snapshot/{lane_id}")
def video_snapshot(lane_id: int):
    from backend.main import video_processor
    if lane_id < 0 or lane_id > 3:
        raise HTTPException(status_code=400, detail="Invalid lane")
    frame = video_processor.get_frame(lane_id)
    if frame:
        return Response(content=frame, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Not Ready")


# ========================
# DASHBOARD STATUS
# ========================
@router.get("/status")
def get_status():
    from backend.main import signal_controller, video_processor
    status = signal_controller.get_status()
    lane_data = video_processor.lane_data
    return {"signal_status": status, "lane_data": lane_data}


# ========================
# CITY MAP DATA
# ========================
@router.get("/city_map_data")
def city_map_data(db: Session = Depends(get_db)):
    from backend.main import signal_controller, video_processor

    status = signal_controller.get_status()
    lane_data = video_processor.lane_data

    reports = db.query(AccidentReport).order_by(AccidentReport.timestamp.desc()).limit(20).all()
    reports_data = [{
        "id": r.id, "location": r.location, "description": r.description,
        "latitude": r.latitude, "longitude": r.longitude, "status": r.status,
        "timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "user": r.user.username if r.user else "Unknown"
    } for r in reports]

    dispatches = db.query(DispatchLog).filter(
        DispatchLog.status.in_(["Dispatched", "En Route", "Arrived", "Patient Loaded"])
    ).order_by(DispatchLog.timestamp.desc()).all()
    dispatch_data = [{
        "id": d.id, "hospital_name": d.hospital_name,
        "hospital_lat": d.hospital_lat, "hospital_lng": d.hospital_lng,
        "accident_lat": d.accident_lat, "accident_lng": d.accident_lng,
        "distance_km": d.distance_km, "status": d.status,
        "timestamp": d.timestamp.strftime("%H:%M:%S")
    } for d in dispatches]

    total_vehicles = sum(lane_data.get(i, {}).get("count", 0) for i in range(4))
    active_incidents = db.query(AccidentReport).filter(AccidentReport.status != "Resolved").count()

    return {
        "signal_status": status, "lane_data": lane_data,
        "reports": reports_data, "dispatches": dispatch_data,
        "summary": {
            "total_vehicles": total_vehicles,
            "active_incidents": active_incidents,
            "active_dispatches": len(dispatch_data)
        }
    }


# ========================
# STATS (Analysis Charts)
# ========================
@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    trend_stats = db.query(LaneStats).order_by(LaneStats.timestamp.desc()).limit(50).all()
    trend_data = [{"time": s.timestamp.strftime("%H:%M:%S"), "count": s.vehicle_count, "lane": s.lane_id} for s in trend_stats]
    trend_data.reverse()

    dist_query = db.query(VehicleLog.vehicle_type, func.sum(VehicleLog.count)).group_by(VehicleLog.vehicle_type).all()
    dist_data = {t: int(c) for t, c in dist_query}

    peak_query = db.query(extract("hour", LaneStats.timestamp).label("h"), func.sum(LaneStats.vehicle_count)).group_by("h").all()
    peak_data = {i: 0 for i in range(24)}
    for h, count in peak_query:
        peak_data[int(h)] = int(count)

    lane_query = db.query(LaneStats.lane_id, func.avg(LaneStats.vehicle_count)).group_by(LaneStats.lane_id).all()
    lane_perf = {int(l): round(float(c), 1) for l, c in lane_query}

    ambulance_events = db.query(DispatchLog).count()

    return {
        "trend": trend_data, "distribution": dist_data,
        "peak_hours": peak_data, "lane_performance": lane_perf,
        "ambulance_events": ambulance_events
    }


# ========================
# REPORTS (Paginated)
# ========================
@router.get("/reports_data")
def reports_data(
    page: int = 1, per_page: int = 20,
    lane: int = None, density: str = None, date: str = None,
    db: Session = Depends(get_db)
):
    per_page = min(per_page, 100)
    query = db.query(LaneStats)

    if lane is not None and 1 <= lane <= 4:
        query = query.filter(LaneStats.lane_id == lane)
    if density and density in ("Low", "Medium", "High"):
        query = query.filter(LaneStats.density == density)
    if date:
        try:
            target = datetime.strptime(date, "%Y-%m-%d")
            query = query.filter(func.date(LaneStats.timestamp) == target.date())
        except ValueError:
            pass

    total = query.count()
    query = query.order_by(LaneStats.timestamp.desc())
    results = query.offset((page - 1) * per_page).limit(per_page).all()

    records = [{
        "id": s.id, "lane_id": s.lane_id, "vehicle_count": s.vehicle_count,
        "density": s.density or ("High" if s.vehicle_count > 20 else ("Medium" if s.vehicle_count > 10 else "Low")),
        "timestamp": s.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    } for s in results]

    total_pages = (total + per_page - 1) // per_page

    return {
        "records": records, "total": total, "pages": total_pages,
        "current_page": page, "per_page": per_page,
        "has_next": page < total_pages, "has_prev": page > 1
    }


# ========================
# EXPORT CSV
# ========================
@router.get("/export_stats")
def export_stats(db: Session = Depends(get_db)):
    stats = db.query(LaneStats).order_by(LaneStats.timestamp.desc()).all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["ID", "Lane ID", "Vehicle Count", "Density Label", "Timestamp"])
    for s in stats:
        cw.writerow([s.id, s.lane_id, s.vehicle_count, s.density, s.timestamp])

    return Response(
        content=si.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=traffic_stats.csv"}
    )


# ========================
# SETTINGS
# ========================
SETTINGS_FILE = os.path.join(settings.BASE_DIR, "system_settings.json")

def _load_settings():
    defaults = {
        "yolo_model": "yolov8s", "confidence_threshold": 45,
        "ambulance_confidence": 65, "low_density_green": 15,
        "medium_density_green": 30, "high_density_green": 45,
        "dark_mode": True, "voice_alerts": True,
        "auto_dispatch": True, "data_retention": "30_days"
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                saved = json.load(f)
            defaults.update(saved)
        except (json.JSONDecodeError, IOError):
            pass
    return defaults

def _save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)

@router.get("/settings")
def get_settings():
    return _load_settings()

@router.post("/settings")
async def save_settings(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    if not body:
        raise HTTPException(status_code=400, detail="No data provided")

    current = _load_settings()
    allowed_keys = {
        "yolo_model", "confidence_threshold", "ambulance_confidence",
        "low_density_green", "medium_density_green", "high_density_green",
        "dark_mode", "voice_alerts", "auto_dispatch", "data_retention"
    }
    for key in allowed_keys:
        if key in body:
            current[key] = body[key]

    _save_settings(current)
    return {"success": True, "settings": current}


# ========================
# PDF / HTML REPORT
# ========================
@router.get("/generate_pdf")
def generate_pdf(db: Session = Depends(get_db)):
    stats = db.query(LaneStats).order_by(LaneStats.timestamp.desc()).limit(100).all()
    dispatches_count = db.query(DispatchLog).count()
    incidents = db.query(AccidentReport).order_by(AccidentReport.timestamp.desc()).limit(20).all()
    incidents_count = db.query(AccidentReport).count()

    total_vehicles = sum(s.vehicle_count for s in stats)
    now = datetime.now()

    rows_html = ""
    for s in stats[:50]:
        density = s.density or ("High" if s.vehicle_count > 20 else ("Medium" if s.vehicle_count > 10 else "Low"))
        rows_html += f"<tr><td>#{s.id}</td><td>Lane {s.lane_id}</td><td>{s.vehicle_count}</td><td>{density}</td><td>{s.timestamp.strftime('%Y-%m-%d %H:%M')}</td></tr>\n"

    inc_rows = ""
    for inc in incidents:
        inc_rows += f"<tr><td>#{inc.id}</td><td>{inc.location}</td><td>{inc.status}</td><td>{inc.timestamp.strftime('%Y-%m-%d %H:%M')}</td></tr>\n"

    html = f"""<html><head><style>
        body {{ font-family: Arial; margin: 40px; color: #1a1a2e; }}
        h1 {{ color: #3b82f6; border-bottom: 3px solid #3b82f6; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 13px; }}
        th {{ background: #3b82f6; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 8px 10px; border-bottom: 1px solid #e2e8f0; }}
    </style></head><body>
        <h1>Traffic Vision AI — Analytics Report</h1>
        <p>Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total Vehicles: {total_vehicles} | Dispatches: {dispatches_count} | Incidents: {incidents_count}</p>
        <h2>Recent Traffic Records</h2>
        <table><tr><th>ID</th><th>Lane</th><th>Vehicles</th><th>Density</th><th>Timestamp</th></tr>{rows_html}</table>
        <h2>Recent Incidents</h2>
        <table><tr><th>ID</th><th>Location</th><th>Status</th><th>Reported</th></tr>{inc_rows}</table>
    </body></html>"""

    return Response(
        content=html, media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename=traffic_report_{now.strftime('%Y%m%d_%H%M%S')}.html"}
    )


# ========================
# SETUP STREAMS (Camera Config)
# ========================
@router.post("/setup_streams")
async def setup_streams(
    cam_1: str = Form(""), cam_2: str = Form(""), cam_3: str = Form(""), cam_4: str = Form(""),
    video_1: UploadFile = File(None), video_2: UploadFile = File(None),
    video_3: UploadFile = File(None), video_4: UploadFile = File(None),
):
    from backend.main import video_processor
    from werkzeug.utils import secure_filename

    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    cams = [cam_1, cam_2, cam_3, cam_4]
    videos = [video_1, video_2, video_3, video_4]
    final_sources = []

    for i in range(4):
        cam_input = cams[i].strip()
        file_obj = videos[i]

        if cam_input:
            if cam_input.isdigit():
                final_sources.append(int(cam_input))
            else:
                final_sources.append(cam_input)
        elif file_obj and file_obj.filename:
            safe_name = secure_filename(file_obj.filename)
            ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
            if ext not in settings.ALLOWED_VIDEO_EXTENSIONS:
                final_sources.append(None)
                continue
            path = os.path.join(settings.UPLOAD_FOLDER, safe_name)
            content = await file_obj.read()
            with open(path, "wb") as f:
                f.write(content)
            final_sources.append(path)
        else:
            final_sources.append(None)

    while len(final_sources) < 4:
        final_sources.append(None)

    video_processor.start_streams(final_sources)
    return {"success": True, "sources": [str(s) for s in final_sources]}


# ========================
# SIGNAL OVERRIDE
# ========================
@router.post("/override")
async def override_signal(request: Request, db: Session = Depends(get_db)):
    from backend.main import signal_controller
    body = await request.json()
    lane_id = int(body.get("lane_id", -1))
    if lane_id < 0 or lane_id > 3:
        raise HTTPException(status_code=400, detail="Invalid lane_id (0-3)")
    success = signal_controller.force_switch(lane_id)
    audit = AuditLog(action="signal_override", details=f"Manual override to Lane {lane_id}")
    db.add(audit)
    db.commit()
    return {"success": success}


# ========================
# AMBULANCE DISPATCH
# ========================
@router.post("/dispatch")
async def dispatch_ambulance(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    report_id = int(body.get("report_id", 0))
    report = db.query(AccidentReport).get(report_id)
    if not report:
        raise HTTPException(status_code=400, detail="Invalid report ID")

    dispatch = DispatchLog(
        report_id=report_id,
        hospital_name=body.get("hospital_name", "Unknown"),
        hospital_lat=body.get("hospital_lat"),
        hospital_lng=body.get("hospital_lng"),
        accident_lat=body.get("accident_lat"),
        accident_lng=body.get("accident_lng"),
        distance_km=body.get("distance_km"),
        status="Dispatched"
    )
    db.add(dispatch)
    db.commit()
    return {"success": True, "dispatch_id": dispatch.id}

@router.get("/dispatch/active")
def get_active_dispatches(db: Session = Depends(get_db)):
    dispatches = db.query(DispatchLog).filter(
        DispatchLog.status.in_(["Dispatched", "En Route", "Arrived", "Patient Loaded"])
    ).order_by(DispatchLog.timestamp.desc()).all()
    return {"dispatches": [{
        "id": d.id, "report_id": d.report_id,
        "hospital_name": d.hospital_name,
        "hospital_lat": d.hospital_lat, "hospital_lng": d.hospital_lng,
        "accident_lat": d.accident_lat, "accident_lng": d.accident_lng,
        "distance_km": d.distance_km, "status": d.status,
        "timestamp": d.timestamp.strftime("%H:%M:%S"),
        "description": d.report.description if d.report else "",
        "location": d.report.location if d.report else ""
    } for d in dispatches]}

@router.post("/dispatch/{dispatch_id}/accept")
def accept_dispatch(dispatch_id: int, db: Session = Depends(get_db)):
    d = db.query(DispatchLog).get(dispatch_id)
    if not d:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    d.status = "En Route"
    db.commit()
    return {"success": True}

@router.post("/dispatch/{dispatch_id}/decline")
def decline_dispatch(dispatch_id: int, db: Session = Depends(get_db)):
    d = db.query(DispatchLog).get(dispatch_id)
    if not d:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    d.status = "Declined"
    db.commit()
    return {"success": True}

@router.post("/dispatch/{dispatch_id}/status")
async def update_dispatch_status(dispatch_id: int, request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    d = db.query(DispatchLog).get(dispatch_id)
    if not d:
        raise HTTPException(status_code=404, detail="Dispatch not found")
    new_status = body.get("status", "")
    valid = ["Dispatched", "En Route", "Arrived", "Patient Loaded", "Complete", "Declined"]
    if new_status not in valid:
        raise HTTPException(status_code=400, detail="Invalid status value")
    d.status = new_status
    db.commit()
    return {"success": True, "status": new_status}


# ========================
# DATA PURGE
# ========================
@router.post("/purge_data")
def purge_data(db: Session = Depends(get_db)):
    lane_count = db.query(LaneStats).count()
    vehicle_count = db.query(VehicleLog).count()
    db.query(LaneStats).delete()
    db.query(VehicleLog).delete()
    db.commit()
    audit = AuditLog(action="data_purge", details=f"Purged {lane_count} lane stats, {vehicle_count} vehicle logs")
    db.add(audit)
    db.commit()
    return {"success": True, "purged": {"lane_stats": lane_count, "vehicle_logs": vehicle_count}}


# ========================
# AUDIT TRAIL
# ========================
@router.get("/audit_trail")
def audit_trail(page: int = 1, per_page: int = 50, db: Session = Depends(get_db)):
    per_page = min(per_page, 100)
    total = db.query(AuditLog).count()
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).offset((page - 1) * per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page

    return {
        "entries": [{
            "id": l.id, "action": l.action, "details": l.details,
            "user": l.user.username if l.user else "System",
            "ip": l.ip_address, "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        } for l in logs],
        "total": total, "pages": total_pages, "current_page": page
    }


# ========================
# AI CONGESTION PREDICTIONS
# ========================
@router.get("/predictions")
def get_predictions(db: Session = Depends(get_db)):
    now = datetime.now()
    predictions = []

    for offset in range(1, 7):
        target_hour = (now.hour + offset) % 24
        avg_result = db.query(func.avg(LaneStats.vehicle_count)).filter(
            extract("hour", LaneStats.timestamp) == target_hour
        ).scalar()
        avg_count = round(float(avg_result or 0), 1)

        if avg_count > 25:
            level, color = "High", "#ef4444"
        elif avg_count > 12:
            level, color = "Medium", "#f59e0b"
        else:
            level, color = "Low", "#10b981"

        predictions.append({
            "hour": f"{target_hour:02d}:00",
            "label": (now + timedelta(hours=offset)).strftime("%I %p"),
            "avg_vehicles": avg_count, "level": level, "color": color,
            "confidence": min(95, 60 + int(avg_count * 0.8))
        })

    peak_hour = max(predictions, key=lambda x: x["avg_vehicles"])
    return {
        "predictions": predictions, "peak_prediction": peak_hour,
        "model": "Historical Time-Series Average",
        "generated_at": now.strftime("%H:%M:%S")
    }


# ========================
# CREATE ADMIN (utility)
# ========================
@router.post("/create_admin")
def create_admin(db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == "admin").first()
    if existing:
        return {"message": "Admin user already exists"}
    user = User(
        username="admin", role="admin",
        password_hash=pwd_context.hash("admin123"),
        full_name="System Admin"
    )
    db.add(user)
    db.commit()
    return {"message": "Admin user created (admin/admin123)"}


# ========================
# USER REGISTRATION
# ========================
@router.post("/auth/register")
async def register(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    username = body.get("username", "").strip()
    full_name = body.get("full_name", "").strip()
    phone_number = body.get("phone_number", "").strip()
    organization = body.get("organization", "").strip()
    password = body.get("password", "")
    confirm_password = body.get("confirm_password", "")

    if not username or len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if not full_name:
        raise HTTPException(status_code=400, detail="Full Name is required")
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=username, full_name=full_name,
        phone_number=phone_number, organization=organization,
        password_hash=pwd_context.hash(password), role="user"
    )
    db.add(user)
    db.commit()
    return {"success": True, "message": "Registration successful"}


# ========================
# ACCIDENT REPORTING
# ========================
@router.post("/report_accident")
async def report_accident(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    location = body.get("location", "").strip()
    description = body.get("description", "").strip()
    latitude = body.get("latitude")
    longitude = body.get("longitude")
    user_id = body.get("user_id")

    if not location:
        raise HTTPException(status_code=400, detail="Location is required")

    try:
        lat_val = float(latitude) if latitude else None
    except (ValueError, TypeError):
        lat_val = None
    try:
        lng_val = float(longitude) if longitude else None
    except (ValueError, TypeError):
        lng_val = None

    report = AccidentReport(
        user_id=user_id, location=location,
        description=description, latitude=lat_val,
        longitude=lng_val, status="Reported"
    )
    db.add(report)
    db.commit()
    return {"success": True, "report_id": report.id}


@router.get("/reports")
def get_reports(db: Session = Depends(get_db)):
    import html as _html
    reports = db.query(AccidentReport).order_by(AccidentReport.timestamp.desc()).limit(20).all()
    return {"reports": [{
        "id": r.id, "location": _html.escape(r.location or ""),
        "description": _html.escape(r.description or ""),
        "latitude": r.latitude, "longitude": r.longitude,
        "timestamp": r.timestamp.strftime("%H:%M:%S"),
        "status": r.status,
        "user": _html.escape(r.user.username) if r.user else "Unknown"
    } for r in reports]}


# ========================
# ADMIN: USER MANAGEMENT
# ========================
@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return {"users": [{
        "id": u.id, "username": u.username, "full_name": u.full_name,
        "phone_number": u.phone_number, "organization": u.organization,
        "role": u.role, "is_locked": u.is_locked,
        "created_at": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else ""
    } for u in users]}


@router.post("/users/{user_id}/unlock")
def unlock_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_locked = False
    user.failed_login_attempts = 0
    db.commit()
    return {"success": True}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete admin user")
    db.delete(user)
    db.commit()
    return {"success": True}

