from app import app, db
from models import User
from werkzeug.security import generate_password_hash
import logging

def create_admin():
    with app.app_context():
        try:
            # Check if admin already exists
            admin = User.query.filter_by(username='admin').first()
            if admin:
                print("Admin user already exists!")
                return

            # Create admin user with empty registration_code
            admin = User(
                username='admin',
                email='admin@schoolhub.com',
                role='admin',
                first_name='Admin',
                last_name='User',
                registration_code_used=''  # Set empty string as default
            )
            admin.set_password('admin123')  # Use the proper method instead of direct hash assignment

            # Add to database
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123")
        except Exception as e:
            print(f"Error creating admin: {e}")
            db.session.rollback()  # Rollback on failure

if __name__ == "__main__":
    create_admin()