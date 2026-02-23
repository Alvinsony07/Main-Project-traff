from app import app
from database.db import db
from database.models import User

with app.app_context():
    print("--- User Debug Info ---")
    users = User.query.all()
    for u in users:
        print(f"ID: {u.id}, Username: {u.username}, Role: {getattr(u, 'role', 'MISSING')}, Password Hash Valid: {bool(u.password_hash)}")
    
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print(f"\nVerifying admin password 'admin123': {admin.check_password('admin123')}")
    else:
        print("\nAdmin user NOT found.")
