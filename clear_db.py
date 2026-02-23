from app import app
from database.db import db
from database.models import VehicleLog, LaneStats, AmbulanceEvent, AccidentReport

with app.app_context():
    print("Clearing all existing data (fake entries)...")
    db.session.query(VehicleLog).delete()
    db.session.query(LaneStats).delete()
    db.session.query(AmbulanceEvent).delete()
    db.session.query(AccidentReport).delete()
    db.session.commit()
    print("Database cleared successfully.")
