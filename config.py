import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-very-secret'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'traffic.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folder for video files
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    
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
