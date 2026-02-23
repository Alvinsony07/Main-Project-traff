from app import app
from database.db import db
from database.models import LaneStats, VehicleLog, AmbulanceEvent, AccidentReport, User

def seed_data():
    with app.app_context():
        print("Seed script running... (Skipping fake data generation as per user request)")
        # Optionally we could clear data here, but that might be destructive to real data.
        # For now, we simply do NOT add any new fake data.
        
if __name__ == "__main__":
    seed_data()
