# Traffic Vision AI v3.0

**AI-Powered Autonomous Traffic Management System using Computer Vision & Deep Learning**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-purple.svg)](https://docs.ultralytics.com/)

---

## Overview

Traffic Vision AI is an intelligent, real-time traffic management system that leverages **YOLOv8 computer vision** for multi-lane vehicle detection, ambulance priority routing, and adaptive signal control. It provides a feature-rich web dashboard for traffic operators, city administrators, and emergency responders.

## Key Features

### 🎯 Computer Vision & AI
- **4-Lane Simultaneous Processing**: Handles 4 video feeds (RTSP streams or local files) concurrently
- **YOLOv8 Vehicle Detection**: Classifies Cars, Trucks, Bikes, Buses, and Auto-Rickshaws
- **Ambulance Detection**: Dual-detection system (YOLO model + color analysis) for emergency vehicle identification
- **Adaptive Signal Control**: Dynamic green light duration based on real-time traffic density

### 🖥️ Dashboard & Analytics
- **Command Center**: Real-time traffic monitoring with live video feeds and signal states
- **City Surveillance Map**: Leaflet.js-based map with junction markers, incident tracking, and hospital routes
- **Advanced Analytics**: Chart.js visualizations (traffic trends, vehicle composition, peak hours, lane load)
- **Reports & Logs**: Server-side paginated historical data with filtering, export to CSV/PDF

### 🚑 Emergency Response
- **Ambulance Priority System**: Auto-clears detected ambulance lanes with green signal
- **Incident Reporting**: Public user portal for accident reporting with GPS location
- **Dispatch Management**: Admin tools for dispatching ambulances to incidents
- **Ambulance Driver Portal**: Dedicated mobile-first interface for emergency drivers

### 🔐 Security
- **Role-based Access Control**: Admin, User, and Driver portals
- **Scrypt Password Hashing**: Industry-standard password security
- **Login Rate Limiting**: Protection against brute-force attacks
- **Account Lockout**: Auto-locks accounts after 5 failed attempts
- **Session Security**: HTTPOnly cookies, SameSite policy, 30-minute timeout

## Quick Start (Windows)

1. **Double-click** `run_project.bat` to automatically:
   - Create virtual environment & install dependencies
   - Initialize the database and create admin user
   - Start the web server

2. Open `http://localhost:5000`

3. Default admin credentials are created during setup. **Change them immediately after first login.**

## Manual Setup

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Installation

```bash
# Navigate to the project folder
cd traffic_vision_ai

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Setup database & admin user
flask --app app create-admin

# Start the server
python app.py
```

Open your browser: `http://localhost:5000`

## Running a Simulation

1. Login to the admin dashboard
2. Navigate to **Camera Config** in the sidebar
3. Upload up to 4 video files (MP4) representing the 4 lanes
4. Click **Start Streams** — the AI pipeline begins processing

## Project Architecture

```
traffic_vision_ai/
├── app.py                  # Flask application, routes, API endpoints
├── config.py               # Security config, model paths, thresholds
├── requirements.txt        # Python dependencies
├── database/
│   ├── db.py               # SQLAlchemy initialization
│   └── models.py           # DB models (User, LaneStats, VehicleLog, etc.)
├── models/
│   ├── vehicle_detector.py # YOLOv8 vehicle classification
│   ├── ambulance_detector.py # Ambulance detection (YOLO + color)
│   ├── signal_controller.py  # Traffic signal state management
│   └── traffic_logic.py    # Density calculation & timing logic
├── utils/
│   └── video_processor.py  # Multi-threaded video stream processing
├── blueprints/
│   └── user.py             # User registration & public reporting routes
├── templates/              # Jinja2 HTML templates
│   ├── index.html          # Landing page
│   ├── dashboard.html      # Admin command center
│   ├── analysis.html       # Analytics dashboard
│   ├── city_overview.html  # City map surveillance
│   ├── ambulance.html      # Emergency driver portal
│   ├── reports.html        # Historical logs & PDF export
│   ├── settings.html       # System configuration
│   ├── camera_config.html  # Camera feed setup
│   ├── login.html          # Authentication
│   ├── partials/           # Reusable UI components
│   │   └── sidebar.html    # Navigation sidebar
│   └── user/
│       ├── dashboard.html  # Public user portal
│       └── register.html   # User registration
├── static/
│   └── css/style.css       # Global stylesheet
└── weights/                # YOLO model weights (not tracked in git)
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Flask 3.x |
| AI/ML | YOLOv8 (Ultralytics), OpenCV |
| Database | SQLite + SQLAlchemy ORM |
| Frontend | HTML5, CSS3 (Custom dark theme), JavaScript |
| Mapping | Leaflet.js with Google Maps tiles |
| Charts | Chart.js |
| Auth | Scrypt hashing, session-based auth |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | Real-time signal & lane data |
| GET | `/api/stats` | Analytics data (trends, distribution) |
| GET | `/api/reports_data` | Paginated reports with filters |
| GET | `/api/settings` | Load system settings |
| POST | `/api/settings` | Save system settings |
| POST | `/api/override` | Manual signal override |
| POST | `/api/dispatch` | Create ambulance dispatch |
| GET | `/api/generate_pdf` | Download traffic report |
| GET | `/api/export_stats` | Export CSV data |

## License

This project is developed for academic and professional purposes.

---

**Traffic Vision AI v3.0** — Autonomous Traffic Intelligence
