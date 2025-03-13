from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, SubmitField, BooleanField, FileField, IntegerField, DateField, FloatField
from wtforms.validators import DataRequired, Email, Length, EqualTo, URL, Optional, ValidationError
from models import RegistrationCode, User, Teacher

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                   validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    class_name = StringField('Class', validators=[DataRequired()])
    registration_code = StringField('Registration Code', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        user = User.query.filter_by(email=field.data).first()
        teacher = Teacher.query.filter_by(email=field.data).first()
        if user or teacher:
            raise ValidationError('Email already registered. Please use a different email.')

    def validate_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        teacher = Teacher.query.filter_by(username=field.data).first()
        if user or teacher:
            raise ValidationError('Username already taken. Please choose a different one.')

    def validate_registration_code(self, field):
        code = RegistrationCode.query.filter_by(code=field.data, is_used=False).first()
        if not code:
            raise ValidationError('Invalid or already used registration code')

class TeacherRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password',
                                   validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired()])
    qualification = StringField('Qualification', validators=[DataRequired()])
    registration_code = StringField('Registration Code', validators=[DataRequired()])
    submit = SubmitField('Register as Teacher')

    def validate_email(self, field):
        user = User.query.filter_by(email=field.data).first()
        teacher = Teacher.query.filter_by(email=field.data).first()
        if user or teacher:
            raise ValidationError('Email already registered. Please use a different email.')

    def validate_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        teacher = Teacher.query.filter_by(username=field.data).first()
        if user or teacher:
            raise ValidationError('Username already taken. Please choose a different one.')

    def validate_registration_code(self, field):
        code = RegistrationCode.query.filter_by(code=field.data, is_used=False, role='teacher').first()
        if not code:
            raise ValidationError('Invalid or already used teacher registration code')

class RegistrationCodeForm(FlaskForm):
    role = SelectField('Role', choices=[('student', 'Student'), ('teacher', 'Teacher')])
    submit = SubmitField('Generate Code')

class AssignmentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[DataRequired()])
    class_name = SelectField('Class', validators=[DataRequired()], choices=[])
    subject = SelectField('Subject', validators=[DataRequired()], choices=[])
    file = FileField('Assignment File')
    submit = SubmitField('Create Assignment')

class SubmitAssignmentForm(FlaskForm):
    file = FileField('Assignment File', validators=[DataRequired()])
    comments = TextAreaField('Comments')
    submit = SubmitField('Submit Assignment')

class AttendanceForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late')
    ])
    submit = SubmitField('Mark Attendance')

class StudentProgressForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired()])
    grade = StringField('Grade', validators=[DataRequired()])
    remarks = TextAreaField('Remarks')
    term = SelectField('Term', choices=[
        ('first_term', 'First Term'),
        ('second_term', 'Second Term'),
        ('third_term', 'Third Term')
    ])
    academic_year = StringField('Academic Year', validators=[DataRequired()])
    submit = SubmitField('Save Progress')

class TCRequestForm(FlaskForm):
    reason = TextAreaField('Reason for TC Request', validators=[DataRequired()])
    submit = SubmitField('Submit Request')

class AnnouncementForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    attachment = FileField('Attachment')
    submit = SubmitField('Post Announcement')

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')

class BannerForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    image = FileField('Banner Image', validators=[DataRequired()])
    link_url = StringField('Link URL', validators=[Optional(), URL()])
    is_active = BooleanField('Active')
    order = IntegerField('Display Order', default=0)
    submit = SubmitField('Save Banner')

class DocumentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    document_type = SelectField('Document Type', choices=[
        ('certificate', 'Certificate'),
        ('form', 'Form'),
        ('notice', 'Notice'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    document = FileField('Document File', validators=[DataRequired()])
    is_public = BooleanField('Public Access', default=True)
    submit = SubmitField('Upload Document')

class MediaForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    media_type = SelectField('Media Type', choices=[
        ('photo', 'Photo'),
        ('video', 'Video')
    ], validators=[DataRequired()])
    media_file = FileField('Media File')
    video_url = StringField('Video URL (YouTube/Facebook)')
    video_platform = SelectField('Video Platform', choices=[
        ('youtube', 'YouTube'),
        ('facebook', 'Facebook'),
        ('other', 'Other')
    ])
    thumbnail = FileField('Thumbnail (for videos)')
    gallery_category = SelectField('Gallery Category')
    is_featured = BooleanField('Featured')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Upload Media')

class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password',
                                   validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class ContentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    page_key = StringField('Page Identifier', validators=[DataRequired()])
    is_published = BooleanField('Published', default=True)
    submit = SubmitField('Save Content')

class PopupBannerForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content')
    image = FileField('Banner Image')
    is_active = BooleanField('Active')
    start_date = DateField('Start Date')
    end_date = DateField('End Date')
    submit = SubmitField('Save Popup Banner')

class GalleryCategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Save Category')

class GalleryItemForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    image = FileField('Image', validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    is_featured = BooleanField('Featured')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Upload Image')

class FeeStructureForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    class_name = StringField('Class', validators=[Optional()])
    fee_type = SelectField('Fee Type', choices=[
        ('comprehensive', 'Comprehensive Fee Structure'),
        ('tuition', 'Tuition Fee'),
        ('hostel', 'Hostel Fee'),
        ('transport', 'Transport Fee'),
        ('other', 'Other Fee')
    ], validators=[Optional()])
    amount = FloatField('Amount', validators=[Optional()])
    academic_year = StringField('Academic Year', validators=[DataRequired()])
    payment_frequency = SelectField('Payment Frequency', choices=[
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually')
    ], validators=[Optional()])
    file = FileField('Fee Structure Document (PDF/Image)')
    notes = TextAreaField('Notes')
    is_active = BooleanField('Active')
    submit = SubmitField('Save Fee Structure')

class PublicDisclosureForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('mandatory', 'Mandatory Disclosure'),
        ('general', 'General Information'),
        ('financial', 'Financial Information'),
        ('academic', 'Academic Information')
    ], validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    file = FileField('Attachment')
    is_active = BooleanField('Active')
    display_order = IntegerField('Display Order', default=0)
    submit = SubmitField('Save Disclosure')

class ContactResponseForm(FlaskForm):
    response = TextAreaField('Response', validators=[DataRequired()])
    submit = SubmitField('Send Response')