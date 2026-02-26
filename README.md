# Traffic Vision AI

AI-powered Intelligent Traffic Management System using Computer Vision.

## Features
- **4-Lane Traffic Monitoring**: Processes 4 video feeds simultaneously.
- **YOLOv8 Detection**: Detects vehicles (Cars, Trucks, Bikes, Buses) and Ambulances.
- **Smart Signaling**: Dynamic Green light duration based on density.
- **Ambulance Priority**: Automatically detects ambulances and clears the lane (Green Signal).
- **Web Dashboard**: Real-time view of traffic, signals, and stats.

## Quick Start (Windows)

1. **Double-click** `run_project.bat` to automatically:
   - Install dependencies.
   - Create the database and admin user.
   - Start the web server.

2. Open `http://localhost:5000`.
3. Login with:
   - **Username**: `admin`
   - **Password**: `admin123`

## Manual Setup Instructions

### 1. Prerequisites
- Python 3.10 or higher
- Windows/Linux/Mac

### 2. Installation
1. Navigate to the project folder:
   ```bash
   cd traffic_vision_ai
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Setup Database & Admin:
   ```bash
   flask --app app create-admin
   ```

### 3. Running the Application
1. Start the Flask server:
   ```bash
   python app.py
   ```
2. Open your browser and go to:
   `http://localhost:5000`

### 4. Running a Simulation
1. Once logged in, you will see the dashboard.
2. In the "Configuration & Controls" section at the bottom, upload up to 4 video files (MP4) representing the 4 lanes.
3. Click "Start Simulation".
4. The system will start processing the videos.

### Project Structure
- `app.py`: Main web server and logic integration.
- `models/`: Contains AI models and Signal Logic.
- `utils/`: Video processing and threading.
- `templates/` & `static/`: Frontend UI.
