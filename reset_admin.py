"""Reset admin user with encrypted credentials (scrypt hash)"""
from app import app
from database.db import db
from database.models import User

with app.app_context():
    # Ensure new columns exist (adds columns if missing)
    db.create_all()
    
    # 1. Delete existing admin
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print(f"Deleting existing admin user (ID: {admin.id})")
        db.session.delete(admin)
        db.session.commit()
    else:
        print("Admin user not found, nothing to delete.")

    # 2. Create fresh admin with scrypt-encrypted password
    print("Creating new admin user with scrypt encryption...")
    new_admin = User(username='admin', role='admin')
    new_admin.set_password('admin123')
    db.session.add(new_admin)
    db.session.commit()
    
    # 3. Verify the hash is scrypt
    print(f"Password hash method: {new_admin.password_hash.split('$')[0]}")
    print(f"Hash length: {len(new_admin.password_hash)} chars")
    print(f"Verification test: {new_admin.check_password('admin123')}")
    print()
    print("Admin user recreated successfully: admin / admin123")
    print("Password is encrypted with scrypt (industry-grade hashing)")
