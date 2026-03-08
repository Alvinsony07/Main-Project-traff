import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    backend_cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    database_url: str = "postgresql://postgres:postgres@localhost/traffic"
    secret_key: str = "your-secret-key"
    
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_FOLDER: str = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH: int = 50 * 1024 * 1024
    ALLOWED_VIDEO_EXTENSIONS: set[str] = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    
    MODEL_VEHICLE_PATH: str = os.path.join(BASE_DIR, 'weights', 'yolov8_vehicle.pt')
    MODEL_AMBULANCE_PATH: str = os.path.join(BASE_DIR, 'weights', 'ambulance.pt')

    MIN_GREEN_TIME: int = 10
    MAX_GREEN_TIME: int = 120
    YELLOW_TIME: int = 3
    DENSITY_LOW: int = 10
    DENSITY_HIGH: int = 30

settings = Settings()
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
