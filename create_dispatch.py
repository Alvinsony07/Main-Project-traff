from app import app, db
from database.models import User, AccidentReport, DispatchLog

with app.app_context():
    # Make sure we have an accident report
    report = AccidentReport.query.filter_by(id=1).first()
    if not report:
        user = User.query.first()
        if not user:
            user = User(username='test', role='user', password_hash='x')
            db.session.add(user)
            db.session.commit()
        report = AccidentReport(user_id=user.id, location='Test St', description='Test accident', latitude=12.0, longitude=77.0)
        db.session.add(report)
        db.session.commit()
    
    dispatch = DispatchLog(
        report_id=report.id,
        hospital_name='City Gen',
        hospital_lat=12.01,
        hospital_lng=77.01,
        accident_lat=report.latitude,
        accident_lng=report.longitude,
        distance_km=1.2,
        status='Dispatched'
    )
    db.session.add(dispatch)
    db.session.commit()
    print('Dispatch created:', dispatch.id)
