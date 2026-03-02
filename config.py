import os
import secrets

def _get_or_create_secret_key():
    """Generate a secret key and persist it so sessions survive restarts."""
    base_dir = os.path.abspath(os.path.dirname(__file__))
    key_file = os.path.join(base_dir, '.secret_key')
    
    # Allow override from environment
    env_key = os.environ.get('SECRET_KEY')
    if env_key:
        return env_key
    
    # Read from file if exists, otherwise generate and save
    if os.path.exists(key_file):
        with open(key_file, 'r') as f:
            return f.read().strip()
    else:
        key = secrets.token_hex(32)
        with open(key_file, 'w') as f:
            f.write(key)
        return key

class Config:
    SECRET_KEY = _get_or_create_secret_key()
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'traffic.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session security
    SESSION_COOKIE_HTTPONLY = True      # Prevent JavaScript access to session cookie
    SESSION_COOKIE_SAMESITE = 'Lax'    # Prevent CSRF via cross-site requests
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes session timeout
    
    # Upload security
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB max upload size
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    
    # Model Paths
    MODEL_VEHICLE_PATH = os.path.join(BASE_DIR, 'weights', 'yolov8_vehicle.pt')
    MODEL_AMBULANCE_PATH = os.path.join(BASE_DIR, 'weights', 'ambulance.pt')

    # Traffic Logic Configuration
    MIN_GREEN_TIME = 10
    MAX_GREEN_TIME = 120
    YELLOW_TIME = 3
    
    # Density Thresholds (Vehicles count)
    DENSITY_LOW = 10
    DENSITY_HIGH = 30
    
    # Ensure upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
