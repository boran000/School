
from app import app, db
from models import User, RegistrationCode, Announcement, Assignment, StudentProgress
from models import TransferCertificate, Attendance, Banner, Document, Media, Content
from models import PopupBanner, GalleryCategory, GalleryItem, FeeStructure, PublicDisclosure, ContactMessage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_database():
    with app.app_context():
        try:
            logger.info("Creating database tables...")
            db.create_all()
            logger.info("Database tables created successfully!")
            
            # Create a sample registration code for admin
            admin_code = RegistrationCode(
                code="ADMIN2024",
                role="admin",
                is_used=False
            )
            db.session.add(admin_code)
            db.session.commit()
            logger.info("Added admin registration code: ADMIN2024")
            
            # Create registration codes for teachers and students
            teacher_code = RegistrationCode(
                code="TEACHER2024",
                role="teacher",
                is_used=False
            )
            student_code = RegistrationCode(
                code="STUDENT2024",
                role="student",
                is_used=False
            )
            db.session.add_all([teacher_code, student_code])
            db.session.commit()
            logger.info("Added teacher and student registration codes")
            
            logger.info("Database initialization complete!")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            db.session.rollback()

if __name__ == "__main__":
    initialize_database()
