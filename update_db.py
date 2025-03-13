from app import app, db
from models import User, RegistrationCode, Teacher, Assignment, Attendance
from sqlalchemy import inspect, text


def update_database_schema():
    with app.app_context():
        inspector = inspect(db.engine)

        # Check if 'role' column exists in 'teacher' table
        teacher_columns = [column['name'] for column in inspector.get_columns('teacher')]

        if 'role' not in teacher_columns:
            print("Adding 'role' column to teacher table...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE teacher ADD COLUMN role VARCHAR(20) DEFAULT 'teacher'"))
                conn.commit()
            print("Column 'role' added successfully to teacher table!")

        # Check if 'class_name' column exists in 'user' table
        user_columns = [column['name'] for column in inspector.get_columns('user')]

        if 'class_name' not in user_columns:
            print("Adding 'class_name' column to user table...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE user ADD COLUMN class_name VARCHAR(20)"))
                conn.commit()
            print("Column 'class_name' added successfully to user table!")

        # Check if new columns exist in 'assignment' table
        assignment_columns = [column['name'] for column in inspector.get_columns('assignment')]

        if 'class_name' not in assignment_columns:
            print("Adding 'class_name' column to assignment table...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE assignment ADD COLUMN class_name VARCHAR(20)"))
                conn.commit()
            print("Column 'class_name' added successfully to assignment table!")

        if 'subject' not in assignment_columns:
            print("Adding 'subject' column to assignment table...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE assignment ADD COLUMN subject VARCHAR(50)"))
                conn.commit()
            print("Column 'subject' added successfully to assignment table!")

        db.create_all()
        print("Database schema updated successfully!")


if __name__ == "__main__":
    update_database_schema()