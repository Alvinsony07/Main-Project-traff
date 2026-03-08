import threading
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database.database import engine, SessionLocal
from backend.database import models
from backend.api import router as api_router
from backend.cv.signal_controller import SignalController
from backend.utils.video_processor import VideoProcessor
from passlib.context import CryptContext

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Traffic Vision AI", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router.router, prefix="/api")

signal_controller = SignalController(num_lanes=4)
video_processor = VideoProcessor(settings, signal_controller)

@app.on_event("startup")
def startup_event():
    # Create default admin user if not exists
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    db = SessionLocal()
    try:
        existing = db.query(models.User).filter(models.User.username == "admin").first()
        if not existing:
            user = models.User(
                username="admin", role="admin",
                password_hash=pwd_context.hash("admin123"),
                full_name="System Admin"
            )
            db.add(user)
            db.commit()
            print("Admin user created (admin/admin123)")
        else:
            print("Admin user already exists.")
    finally:
        db.close()

    # Start signal controller background thread
    def signal_timer_loop():
        while True:
            time.sleep(1)
            if video_processor:
                def get_all_counts():
                    return {i: video_processor.get_lane_count(i) for i in range(4)}
                signal_controller.update_state(time.time(), get_all_counts, video_processor.traffic_logic)

    signal_thread = threading.Thread(target=signal_timer_loop, daemon=True)
    signal_thread.start()

@app.on_event("shutdown")
def shutdown_event():
    video_processor.stop()

@app.get("/")
def read_root():
    return {"message": "Traffic Vision AI API Backend"}
