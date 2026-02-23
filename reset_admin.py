from app import app
from database.db import db
from database.models import User

with app.app_context():
    # 1. Delete existing admin
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print(f"Deleting existing admin user (ID: {admin.id})")
        db.session.delete(admin)
        db.session.commit()
    else:
        print("Admin user not found, nothing to delete.")

    # 2. Create fresh admin
    print("Creating new admin user...")
    new_admin = User(username='admin', role='admin')
    new_admin.set_password('admin123')
    db.session.add(new_admin)
    db.session.commit()
    
    print("Admin user recreated successfully: admin / admin123")
