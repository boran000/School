from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


# The user_loader function is now implemented in app.py
# This function is no longer needed here


class RegistrationCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student, teacher
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_by = db.Column(db.Integer)  # Generic ID field without foreign key constraint
    # This will be either a user.id or teacher.id depending on the role


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), nullable=False)  # admin, student
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    registration_code_used = db.Column(db.String(20))
    class_name = db.Column(db.String(20), nullable=True)  # Added field for student's class

    # Relationships for students
    assignments_received = db.relationship('Assignment', backref='student', lazy=True,
                                           foreign_keys='Assignment.student_id')
    attendances = db.relationship('Attendance', backref='student', lazy=True,
                                  foreign_keys='Attendance.student_id')

    # Teacher relationship
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_url = db.Column(db.String(255))


class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    file_url = db.Column(db.String(255))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    class_name = db.Column(db.String(20))  # Added field for class
    subject = db.Column(db.String(50))     # Added field for subject
    status = db.Column(db.String(20), default='pending')  # pending, submitted, graded
    grade = db.Column(db.String(5))
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Teacher(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    registration_code_used = db.Column(db.String(20))
    subject = db.Column(db.String(100))
    qualification = db.Column(db.String(100))
    role = db.Column(db.String(20), default='teacher')

    # Relationships
    students = db.relationship('User', backref='assigned_teacher', lazy=True,
                               foreign_keys='User.teacher_id')
    assignments_given = db.relationship('Assignment', backref='teacher', lazy=True)
    attendances_marked = db.relationship('Attendance', backref='marked_by_teacher', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class StudentProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subject = db.Column(db.String(100))
    grade = db.Column(db.String(5))
    remarks = db.Column(db.Text)
    term = db.Column(db.String(20))  # First Term, Second Term, etc.
    academic_year = db.Column(db.String(9))  # e.g., 2024-2025
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TransferCertificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tc_number = db.Column(db.String(50), unique=True)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    reason = db.Column(db.Text)
    file_url = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')  # pending, approved, issued
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='present')  # present, absent, late
    marked_by = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Banner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255), nullable=False)
    link_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    document_type = db.Column(db.String(50), nullable=False)  # certificate, form, etc.
    file_url = db.Column(db.String(255), nullable=False)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    media_type = db.Column(db.String(50), nullable=False)  # photo, video
    file_url = db.Column(db.String(255), nullable=False)
    thumbnail_url = db.Column(db.String(255))
    gallery_category = db.Column(db.String(50))
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    video_platform = db.Column(db.String(50))  # youtube, facebook, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    page_key = db.Column(db.String(50), nullable=False, unique=True)  # about, contact, etc.
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PopupBanner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GalleryCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    items = db.relationship('GalleryItem', backref='category', lazy=True)


class GalleryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('gallery_category.id'))
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FeeStructure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    fee_type = db.Column(db.String(50), nullable=False)  # tuition, hostel, transport, etc.
    amount = db.Column(db.Float, nullable=False)
    academic_year = db.Column(db.String(9), nullable=False)  # e.g., 2024-2025
    payment_frequency = db.Column(db.String(20))  # monthly, quarterly, annually
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    file_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PublicDisclosure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # mandatory, general, financial, etc.
    content = db.Column(db.Text, nullable=False)
    file_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, responded, archived
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    response = db.Column(db.Text)
    responded_at = db.Column(db.DateTime)
    responded_by = db.Column(db.Integer, db.ForeignKey('user.id'))