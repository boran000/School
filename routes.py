from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from app import db, app
from models import User, Announcement, Banner, Document, Media, Content, Assignment, Attendance, StudentProgress, \
    TransferCertificate, PopupBanner, GalleryCategory, GalleryItem, FeeStructure, PublicDisclosure, ContactMessage, \
    RegistrationCode, Teacher
from forms import (LoginForm, RegistrationForm, AnnouncementForm, ContactForm,
                   BannerForm, DocumentForm, MediaForm, ContentForm, AssignmentForm, AttendanceForm,
                   StudentProgressForm, SubmitAssignmentForm, TCRequestForm, PopupBannerForm, GalleryCategoryForm,
                   GalleryItemForm, FeeStructureForm, PublicDisclosureForm, ContactResponseForm, RegistrationCodeForm,
                   PasswordChangeForm, TeacherRegistrationForm)
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Create blueprints with URL prefixes
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
main_bp = Blueprint('main', __name__)  # No prefix for main as it contains root routes
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


def register_blueprints(app):
    logger.info("Registering blueprints...")
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(dashboard_bp)
    logger.info("Blueprints registered successfully")


# Diagnostic route
@main_bp.route('/ping')
def ping():
    logger.info("Ping endpoint hit")
    return "pong"


# Main routes
@main_bp.route('/')
def home():
    logger.info("Home route accessed")
    try:
        announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(3).all()
        banners = Banner.query.filter_by(is_active=True).order_by(Banner.order.asc()).all()

        # Debug information
        all_banners = Banner.query.all()
        logger.info(f"Total banners in database: {len(all_banners)}")
        for banner in all_banners:
            logger.info(
                f"Banner ID: {banner.id}, Title: {banner.title}, Active: {banner.is_active}, Order: {banner.order}, Image URL: {banner.image_url}")
            # Check if image file exists
            import os
            image_path = os.path.join(app.static_folder, banner.image_url.replace('/uploads/', 'uploads/'))
            logger.info(f"Checking image path: {image_path}, exists: {os.path.exists(image_path)}")

        logger.info(f"Retrieved {len(announcements)} announcements and {len(banners)} active banners for display")

        # Check if there's an active popup banner - ONLY FOR HOMEPAGE
        show_popup = False
        popup = None

        try:
            # Get the most recent active popup banner
            from datetime import datetime
            now = datetime.utcnow()

            popup_query = PopupBanner.query.filter_by(is_active=True)

            # Apply date filtering if dates are set
            date_filtered_popups = popup_query.filter(
                (PopupBanner.start_date == None) | (PopupBanner.start_date <= now)
            ).filter(
                (PopupBanner.end_date == None) | (PopupBanner.end_date >= now)
            ).order_by(PopupBanner.created_at.desc()).first()

            if date_filtered_popups:
                show_popup = True
                popup = date_filtered_popups
                logger.info(f"Active popup found: {popup.title}")
                if popup.image_url:
                    logger.info(f"Popup image URL: {popup.image_url}")
                    # Check if image file exists
                    import os
                    image_path = os.path.join(app.static_folder, popup.image_url.replace('/uploads/', 'uploads/'))
                    logger.info(f"Checking popup image path: {image_path}, exists: {os.path.exists(image_path)}")
        except Exception as popup_error:
            logger.error(f"Error getting popup banner: {str(popup_error)}")

        return render_template('home.html', announcements=announcements, banners=banners,
                               show_popup=show_popup, popup=popup)
    except Exception as e:
        logger.error(f"Error in home route: {str(e)}")
        return "An error occurred", 500


@main_bp.route('/about')
def about():
    logger.info("About route accessed")
    # No popup on About page
    return render_template('about.html')


@main_bp.route('/academics')
def academics():
    logger.info("Academics route accessed")
    # No popup on Academics page
    return render_template('academics.html')


@main_bp.route('/admissions')
def admissions():
    logger.info("Admissions route accessed")
    return render_template('admissions.html')


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        message = ContactMessage(
            name=form.name.data,
            email=form.email.data,
            subject=form.subject.data,
            message=form.message.data
        )
        db.session.add(message)
        db.session.commit()
        flash('Your message has been sent! We will get back to you soon.', 'success')
        return redirect(url_for('main.contact'))
    return render_template('contact.html', form=form)


@main_bp.route('/news')
def news():
    logger.info("News route accessed")
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('news.html', announcements=announcements, User=User)


# Dashboard routes
@dashboard_bp.route('/')
@login_required
def index():
    logger.info(f"Dashboard route accessed by user: {current_user.username}")
    from datetime import datetime

    # Log important debugging information
    logger.info(f"Current user type: {type(current_user).__name__}")
    if hasattr(current_user, 'role'):
        logger.info(f"User role: {current_user.role}")

    # Check if it's a Teacher instance first
    if isinstance(current_user, Teacher):
        logger.info(f"Rendering teacher dashboard for: {current_user.username}")
        return render_template('dashboard/teacher.html', User=User, Assignment=Assignment,
                               Attendance=Attendance, StudentProgress=StudentProgress,
                               Teacher=Teacher, datetime=datetime)
    # Then check regular user roles
    elif hasattr(current_user, 'role') and current_user.role == 'admin':
        from models import GalleryItem, PopupBanner
        logger.info(f"Rendering admin dashboard for: {current_user.username}")
        return render_template('dashboard/admin.html', User=User, Document=Document, Media=Media, Banner=Banner,
                               Announcement=Announcement, TransferCertificate=TransferCertificate, Content=Content,
                               PublicDisclosure=PublicDisclosure, GalleryItem=GalleryItem, PopupBanner=PopupBanner)
    else:
        logger.info(f"Rendering student dashboard for: {current_user.username}")
        return render_template('dashboard/student.html', StudentProgress=StudentProgress,
                               Assignment=Assignment, TransferCertificate=TransferCertificate,
                               User=User, Announcement=Announcement)


@dashboard_bp.route('/announcements/new', methods=['GET', 'POST'])
@login_required
def new_announcement():
    logger.info(f"New announcement route accessed by user: {current_user.username}")
    if current_user.role not in ['admin', 'teacher']:
        flash('You do not have permission to create announcements.', 'danger')
        return redirect(url_for('dashboard.index'))

    form = AnnouncementForm()
    if form.validate_on_submit():
        file_url = None
        if form.attachment.data:
            attachment = form.attachment.data
            filename = secure_filename(attachment.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'announcements', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            attachment.save(file_path)
            file_url = f'/uploads/announcements/{filename}'

        announcement = Announcement(
            title=form.title.data,
            content=form.content.data,
            author_id=current_user.id,
            file_url=file_url
        )
        db.session.add(announcement)
        db.session.commit()
        flash('Announcement created successfully!', 'success')
        return redirect(url_for('main.news'))
    return render_template('dashboard/new_announcement.html', form=form)


@dashboard_bp.route('/announcements/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_announcement(id):
    logger.info(f"Edit announcement route accessed by user: {current_user.username}")
    if current_user.role not in ['admin', 'teacher']:
        flash('You do not have permission to edit announcements.', 'danger')
        return redirect(url_for('dashboard.index'))

    announcement = Announcement.query.get_or_404(id)
    form = AnnouncementForm(obj=announcement)

    if form.validate_on_submit():
        announcement.title = form.title.data
        announcement.content = form.content.data

        # Handle attachment if provided
        if 'attachment' in request.files and request.files['attachment'].filename:
            attachment = request.files['attachment']
            filename = secure_filename(attachment.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'announcements', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            attachment.save(file_path)
            announcement.file_url = f'/uploads/announcements/{filename}'

        db.session.commit()
        flash('Announcement updated successfully!', 'success')
        return redirect(url_for('dashboard.manage_announcements'))

    return render_template('dashboard/new_announcement.html', form=form, announcement=announcement,
                           title="Edit Announcement")


@dashboard_bp.route('/announcements/manage')
@login_required
def manage_announcements():
    logger.info(f"Manage announcements route accessed by user: {current_user.username}")
    if current_user.role not in ['admin', 'teacher']:
        flash('You do not have permission to manage announcements.', 'danger')
        return redirect(url_for('dashboard.index'))

    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('dashboard/manage_announcements.html', announcements=announcements)


@dashboard_bp.route('/announcements/<int:id>/delete', methods=['POST'])
@login_required
def delete_announcement(id):
    logger.info(f"Delete announcement route accessed by user: {current_user.username}")
    if current_user.role not in ['admin', 'teacher']:
        flash('You do not have permission to delete announcements.', 'danger')
        return redirect(url_for('dashboard.index'))

    announcement = Announcement.query.get_or_404(id)

    try:
        # Delete the attachment file if it exists
        if announcement.file_url:
            file_path = os.path.join(current_app.static_folder, announcement.file_url.lstrip('/'))
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted announcement attachment: {file_path}")

        db.session.delete(announcement)
        db.session.commit()
        flash('Announcement deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting announcement: {str(e)}")
        flash(f'Error deleting announcement: {str(e)}', 'danger')

    return redirect(url_for('dashboard.manage_announcements'))


# CMS Management Routes
@dashboard_bp.route('/banners/new', methods=['GET', 'POST'])
@login_required
def new_banner():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    form = BannerForm()
    if form.validate_on_submit():
        try:
            # Handle file upload
            image = form.image.data
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            filename = secure_filename(f"{timestamp}_{image.filename}")
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'banners', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            image.save(file_path)

            image_url = f'/uploads/banners/{filename}'

            # Debug log
            logger.info(f"Saved banner image to: {file_path}")
            logger.info(f"Image URL set to: {image_url}")

            banner = Banner(
                title=form.title.data,
                description=form.description.data,
                image_url=image_url,
                link_url=form.link_url.data,
                is_active=form.is_active.data,
                order=form.order.data
            )
            db.session.add(banner)
            db.session.commit()
            flash('Banner added successfully!', 'success')
            return redirect(url_for('dashboard.manage_banners'))
        except Exception as e:
            logger.error(f"Error creating banner: {str(e)}")
            flash(f'Error creating banner: {str(e)}', 'danger')

    return render_template('dashboard/banner_form.html', form=form, title='New Banner')


@dashboard_bp.route('/documents/new', methods=['GET', 'POST'])
@login_required
def new_document():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    form = DocumentForm()
    if form.validate_on_submit():
        try:
            # Handle file upload
            doc_file = form.document.data
            filename = secure_filename(doc_file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            doc_file.save(file_path)

            document = Document(
                title=form.title.data,
                description=form.description.data,
                document_type=form.document_type.data,
                file_url=f'/uploads/documents/{filename}',
                is_public=form.is_public.data
            )
            db.session.add(document)
            db.session.commit()
            flash('Document uploaded successfully!', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            flash('Error uploading document. Please try again.', 'danger')

    return render_template('dashboard/document_form.html', form=form, title='Upload Document')


@dashboard_bp.route('/media/new', methods=['GET', 'POST'])
@login_required
def new_media():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    form = MediaForm()

    # Populate categories from GalleryCategory model
    categories = GalleryCategory.query.all()

    if not categories:
        flash('Please create a gallery category first.', 'warning')
        return redirect(url_for('dashboard.new_gallery_category'))

    form.gallery_category.choices = [(c.name, c.name) for c in categories]

    # Ensure video platform choices are set
    form.video_platform.choices = [
        ('youtube', 'YouTube'),
        ('facebook', 'Facebook'),
        ('other', 'Other')
    ]

    if form.validate_on_submit():
        try:
            file_url = None
            video_platform = None
            selected_category = form.gallery_category.data
            category_folder = secure_filename(selected_category.lower().replace(' ', '_'))

            # Handle different media types
            if form.media_type.data == 'video' and form.video_url.data:
                # For video URLs (YouTube, Facebook, etc.)
                file_url = form.video_url.data
                video_platform = form.video_platform.data

                # Log the video URL for debugging
                logger.info(f"Processing video URL: {file_url}, platform: {video_platform}")

                # Clean YouTube URL if needed
                if video_platform == 'youtube' and 'youtube.com' in file_url:
                    # Make sure we're storing a clean URL format
                    if 'watch?v=' in file_url:
                        video_id = file_url.split('watch?v=')[-1].split('&')[0]
                        logger.info(f"Extracted YouTube ID: {video_id}")
                        # Store the original URL as is, we'll extract ID in templates
            elif form.media_file.data:
                # Handle media file upload
                media_file = form.media_file.data
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                filename = secure_filename(f"{timestamp}-{media_file.filename}")

                # Create folder with category name
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'media', category_folder, filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                media_file.save(file_path)
                file_url = f'/uploads/media/{category_folder}/{filename}'
            else:
                flash('Please provide either a video URL or upload a media file.', 'danger')
                return render_template('dashboard/media_form.html', form=form, title='Upload Media')

            # Handle thumbnail if provided (for videos)
            thumbnail_url = None
            if form.thumbnail.data:
                thumb_file = form.thumbnail.data
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                thumb_filename = secure_filename(f"{timestamp}-{thumb_file.filename}")

                # Use same category folder for thumbnails
                thumb_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'thumbnails', category_folder,
                                          thumb_filename)
                os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
                thumb_file.save(thumb_path)
                thumbnail_url = f'/uploads/thumbnails/{category_folder}/{thumb_filename}'

            media = Media(
                title=form.title.data,
                description=form.description.data,
                media_type=form.media_type.data,
                file_url=file_url,
                thumbnail_url=thumbnail_url,
                gallery_category=selected_category,
                is_featured=form.is_featured.data,
                is_active=form.is_active.data,
                video_platform=video_platform
            )
            db.session.add(media)
            db.session.commit()

            logger.info(f"Media added: {media.file_url}, Type: {media.media_type}, Platform: {media.video_platform}")
            flash('Media uploaded successfully!', 'success')
            return redirect(url_for('dashboard.manage_media'))
        except Exception as e:
            logger.error(f"Error uploading media: {str(e)}")
            flash(f'Error uploading media: {str(e)}', 'danger')

    return render_template('dashboard/media_form.html', form=form, title='Upload Media')


@dashboard_bp.route('/media/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_media(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    media = Media.query.get_or_404(id)
    form = MediaForm(obj=media)

    if form.validate_on_submit():
        try:
            media.title = form.title.data
            media.description = form.description.data
            media.gallery_category = form.gallery_category.data
            media.is_featured = form.is_featured.data
            media.is_active = form.is_active.data

            # Update video URL if provided
            if form.media_type.data == 'video' and form.video_url.data:
                media.file_url = form.video_url.data
                media.video_platform = form.video_platform.data

            # Update file if provided
            if form.media_file.data:
                media_file = form.media_file.data
                filename = secure_filename(media_file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'media', filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                media_file.save(file_path)
                media.file_url = f'/uploads/media/{filename}'

            # Update thumbnail if provided
            if form.thumbnail.data:
                thumb_file = form.thumbnail.data
                thumb_filename = secure_filename(thumb_file.filename)
                thumb_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'thumbnails', thumb_filename)
                os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
                thumb_file.save(thumb_path)
                media.thumbnail_url = f'/uploads/thumbnails/{thumb_filename}'

            db.session.commit()
            flash('Media updated successfully!', 'success')
            return redirect(url_for('dashboard.manage_media'))
        except Exception as e:
            logger.error(f"Error updating media: {str(e)}")
            flash('Error updating media. Please try again.', 'danger')

    return render_template('dashboard/media_form.html', form=form, media=media, title='Edit Media')


@dashboard_bp.route('/content/new', methods=['GET', 'POST'])
@login_required
def new_content():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    form = ContentForm()
    if form.validate_on_submit():
        try:
            content = Content(
                title=form.title.data,
                content=form.content.data,
                page_key=form.page_key.data,
                is_published=form.is_published.data
            )
            db.session.add(content)
            db.session.commit()
            flash('Content page created successfully!', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            logger.error(f"Error creating content: {str(e)}")
            flash('Error creating content. Please try again.', 'danger')

    return render_template('dashboard/content_form.html', form=form, title='New Content Page')


@dashboard_bp.route('/content/manage')
@login_required
def manage_content():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    contents = Content.query.order_by(Content.created_at.desc()).all()
    return render_template('dashboard/manage_content.html', contents=contents)


# Edit routes for CMS content
@dashboard_bp.route('/banners/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_banner(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    banner = Banner.query.get_or_404(id)
    form = BannerForm(obj=banner)

    if form.validate_on_submit():
        try:
            banner.title = form.title.data
            banner.description = form.description.data
            banner.link_url = form.link_url.data
            banner.is_active = form.is_active.data
            banner.order = form.order.data

            if form.image.data:
                image = form.image.data
                filename = secure_filename(image.filename)
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'banners', filename)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                image.save(image_path)
                banner.image_url = f'/uploads/banners/{filename}'

            db.session.commit()
            flash('Banner updated successfully!', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            logger.error(f"Error updating banner: {str(e)}")
            flash('Error updating banner. Please try again.', 'danger')

    return render_template('dashboard/banner_form.html', form=form, title='Edit Banner', banner=banner)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    logger.info("Login route accessed")
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        # First check if it's a teacher (check Teacher model first)
        teacher = Teacher.query.filter_by(username=form.username.data).first()
        if teacher and teacher.check_password(form.password.data):
            # Use remember=True to ensure the session cookie has proper duration
            login_user(teacher, remember=True)
            # Add a session marker to help identify the user type
            from flask import session
            session['user_type'] = 'teacher'
            session['user_id'] = teacher.id

            logger.info(f"Teacher {teacher.username} logged in successfully")
            logger.info(f"User type after login: {type(current_user).__name__}")
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard.index'))

        # Then check if it's a regular user
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            # Use remember=True to ensure the session cookie has proper duration
            login_user(user, remember=True)
            # Add a session marker to help identify the user type
            from flask import session
            session['user_type'] = 'user'
            session['user_id'] = user.id

            logger.info(f"User {user.username} with role {user.role} logged in successfully")
            logger.info(f"User type after login: {type(current_user).__name__}")
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard.index'))

        flash('Invalid username or password', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET'])
def register_selection():
    logger.info("Register selection route accessed")
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    return render_template('auth/register_selection.html')


@auth_bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    logger.info("Student register route accessed")
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            # Find the unused registration code
            reg_code = RegistrationCode.query.filter_by(code=form.registration_code.data, is_used=False).first()

            if not reg_code:
                flash('Invalid or already used registration code.', 'danger')
                return render_template('auth/register_student.html', form=form)

            if reg_code.role == 'teacher':
                flash('Please use the teacher registration form for teacher registration codes.', 'danger')
                return redirect(url_for('auth.register_teacher'))

            user = User(
                username=form.username.data,
                email=form.email.data,
                role=reg_code.role,  # Get role from the registration code
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                class_name=form.class_name.data,
                registration_code_used=form.registration_code.data
            )
            user.set_password(form.password.data)

            # Mark the registration code as used
            reg_code.is_used = True

            db.session.add(user)
            db.session.commit()

            reg_code.used_by = user.id
            db.session.commit()

            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during student registration: {str(e)}")
            flash(f'Registration error: {str(e)}', 'danger')
    else:
        # If form validation failed, log the errors
        logger.info(f"Form validation failed: {form.errors}")
        if form.errors:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field}: {error}", 'danger')

    return render_template('auth/register_student.html', form=form)


@auth_bp.route('/register/teacher', methods=['GET', 'POST'])
def register_teacher():
    logger.info("Teacher register route accessed")
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = TeacherRegistrationForm()

    if form.validate_on_submit():
        # Find the unused registration code
        reg_code = RegistrationCode.query.filter_by(code=form.registration_code.data, is_used=False).first()

        if not reg_code:
            flash('Invalid or already used registration code.', 'danger')
            return render_template('auth/register_teacher.html', form=form)

        if reg_code.role != 'teacher':
            flash('This registration code is not for teachers.', 'danger')
            return redirect(url_for('auth.register_student'))

        # Check if username already exists for User or Teacher
        existing_user = User.query.filter_by(username=form.username.data).first()
        existing_teacher = Teacher.query.filter_by(username=form.username.data).first()

        if existing_user or existing_teacher:
            flash('Username already taken. Please choose a different one.', 'danger')
            return render_template('auth/register_teacher.html', form=form)

        # Check if email already exists for User or Teacher
        existing_email_user = User.query.filter_by(email=form.email.data).first()
        existing_email_teacher = Teacher.query.filter_by(email=form.email.data).first()

        if existing_email_user or existing_email_teacher:
            flash('Email already registered. Please use a different email.', 'danger')
            return render_template('auth/register_teacher.html', form=form)

        # Create a new Teacher object, NOT a User with role 'teacher'
        teacher = Teacher(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            subject=form.subject.data,
            qualification=form.qualification.data,
            registration_code_used=form.registration_code.data,
            role='teacher'
        )
        teacher.set_password(form.password.data)

        # Log the registration for debugging
        logger.info(f"Registering new teacher: {teacher.username}, email: {teacher.email}")
        logger.info(f"Teacher type: {type(teacher).__name__}")

        # First save the teacher to get an ID
        db.session.add(teacher)
        db.session.commit()

        # Mark the registration code as used
        reg_code.is_used = True
        reg_code.used_by = teacher.id

        # Make sure we specify used_by references a Teacher model, not User model
        db.session.commit()

        logger.info(f"Teacher created with ID: {teacher.id}")
        logger.info(f"Registration code {reg_code.code} marked as used by teacher ID: {teacher.id}")

        flash('Teacher registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_teacher.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logger.info(f"Logout route accessed by user: {current_user.username}")
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))


# Teacher specific routes
@dashboard_bp.route('/assignments/new', methods=['GET', 'POST'])
@login_required
def new_assignment():
    from models import Teacher, User
    if not isinstance(current_user, Teacher):
        flash('Access denied. Teacher privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    form = AssignmentForm()

    # Get unique class names from students for the class dropdown
    unique_classes = db.session.query(User.class_name).filter(
        User.role == 'student',
        User.class_name != None,
        User.class_name != ''
    ).distinct().all()
    form.class_name.choices = [(c[0], c[0]) for c in unique_classes]

    # Set subject choices based on teacher's subject
    if current_user.subject:
        form.subject.choices = [(current_user.subject, current_user.subject)]
    else:
        form.subject.choices = [('Mathematics', 'Mathematics'),
                                ('Science', 'Science'),
                                ('English', 'English'),
                                ('History', 'History'),
                                ('Geography', 'Geography'),
                                ('Computer Science', 'Computer Science')]

    if form.validate_on_submit():
        try:
            # Handle file upload if present
            file_url = None
            if form.file.data:
                file = form.file.data
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'assignments', filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                file_url = f'/uploads/assignments/{filename}'

            # Get students of the selected class
            students = User.query.filter_by(role='student', class_name=form.class_name.data).all()

            # Create an assignment for each student in the class
            for student in students:
                assignment = Assignment(
                    title=form.title.data,
                    description=form.description.data,
                    due_date=form.due_date.data,
                    file_url=file_url,
                    teacher_id=current_user.id,
                    student_id=student.id,
                    class_name=form.class_name.data,
                    subject=form.subject.data
                )
                db.session.add(assignment)

            db.session.commit()
            flash(f'Assignment created successfully for {len(students)} students in {form.class_name.data}!', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            logger.error(f"Error creating assignment: {str(e)}")
            flash(f'Error creating assignment: {str(e)}', 'danger')

    return render_template('dashboard/assignment_form.html', form=form, title='New Assignment')


@dashboard_bp.route('/attendance/take', methods=['GET', 'POST'])
@login_required
def take_attendance():
    from models import Teacher
    if not isinstance(current_user, Teacher):
        flash('Access denied. Teacher privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    form = AttendanceForm()
    if form.validate_on_submit():
        try:
            # Get all students
            students = User.query.filter_by(role='student').all()
            for student in students:
                attendance = Attendance(
                    student_id=student.id,
                    date=form.date.data,
                    status=request.form.get(f'status_{student.id}', 'absent'),
                    marked_by=current_user.id
                )
                db.session.add(attendance)
            db.session.commit()
            flash('Attendance marked successfully!', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            logger.error(f"Error marking attendance: {str(e)}")
            flash('Error marking attendance. Please try again.', 'danger')

    students = User.query.filter_by(role='student').all()
    return render_template('dashboard/attendance_form.html', form=form, students=students, title='Take Attendance')


@dashboard_bp.route('/progress/record', methods=['GET', 'POST'])
@login_required
def student_progress():
    from models import Teacher
    if not isinstance(current_user, Teacher):
        flash('Access denied. Teacher privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    form = StudentProgressForm()
    if form.validate_on_submit():
        try:
            progress = StudentProgress(
                student_id=request.form.get('student_id'),
                subject=form.subject.data,
                grade=form.grade.data,
                remarks=form.remarks.data,
                term=form.term.data,
                academic_year=form.academic_year.data
            )
            db.session.add(progress)
            db.session.commit()
            flash('Progress recorded successfully!', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            logger.error(f"Error recording progress: {str(e)}")
            flash('Error recording progress. Please try again.', 'danger')

    students = User.query.filter_by(role='student').all()
    return render_template('dashboard/progress_form.html', form=form, students=students, title='Record Progress')


# Student specific routes
@dashboard_bp.route('/assignments/submit/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def submit_assignment(assignment_id):
    if current_user.role != 'student':
        flash('Access denied. Student privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    assignment = Assignment.query.get_or_404(assignment_id)
    form = SubmitAssignmentForm()

    if form.validate_on_submit():
        try:
            file = form.file.data
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'submissions', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)

            assignment.status = 'submitted'
            assignment.file_url = f'/uploads/submissions/{filename}'
            db.session.commit()
            flash('Assignment submitted successfully!', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            logger.error(f"Error submitting assignment: {str(e)}")
            flash('Error submitting assignment. Please try again.', 'danger')

    return render_template('dashboard/submit_assignment.html', form=form, assignment=assignment)


@dashboard_bp.route('/tc/request', methods=['GET', 'POST'])
@login_required
def request_tc():
    if current_user.role != 'student':
        flash('Access denied. Student privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    form = TCRequestForm()
    if form.validate_on_submit():
        try:
            tc = TransferCertificate(
                student_id=current_user.id,
                reason=form.reason.data,
                tc_number=f'TC{current_user.id}-{datetime.utcnow().strftime("%Y%m%d%H%M")}'
            )
            db.session.add(tc)
            db.session.commit()
            flash('Transfer Certificate request submitted successfully!', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            logger.error(f"Error requesting TC: {str(e)}")
            flash('Error requesting TC. Please try again.', 'danger')

    return render_template('dashboard/tc_request.html', form=form)


# Add after existing routes

# Popup Banner Routes
@dashboard_bp.route('/popup-banners/new', methods=['GET', 'POST'])
@login_required
def new_popup_banner():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    form = PopupBannerForm()
    if form.validate_on_submit():
        try:
            image_url = None
            if form.image.data:
                image = form.image.data
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                filename = secure_filename(f"{timestamp}_{image.filename}")
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'popups', filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                image.save(file_path)
                image_url = f'/uploads/popups/{filename}'

                # Debug log
                logger.info(f"Saved popup banner image to: {file_path}")
                logger.info(f"Image URL set to: {image_url}")

            banner = PopupBanner(
                title=form.title.data,
                content=form.content.data,
                image_url=image_url,
                is_active=form.is_active.data,
                start_date=form.start_date.data,
                end_date=form.end_date.data
            )
            db.session.add(banner)
            db.session.commit()
            flash('Popup banner created successfully!', 'success')
            return redirect(url_for('dashboard.manage_popup_banners'))
        except Exception as e:
            logger.error(f"Error creating popup banner: {str(e)}")
            flash(f'Error creating popup banner: {str(e)}', 'danger')

    return render_template('dashboard/popup_banner_form.html', form=form, title='New Popup Banner')


@dashboard_bp.route('/banners/manage')
@login_required
def manage_banners():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    banners = Banner.query.order_by(Banner.order.asc()).all()
    return render_template('dashboard/manage_banners.html', banners=banners)


@dashboard_bp.route('/gallery/manage')
@login_required
def manage_gallery():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    categories = GalleryCategory.query.all()
    photos = GalleryItem.query.order_by(GalleryItem.created_at.desc()).all()
    videos = Media.query.filter_by(media_type='video').order_by(Media.created_at.desc()).all()

    # Create a simple form to provide CSRF token
    from flask_wtf import FlaskForm
    form = FlaskForm()

    return render_template('dashboard/manage_gallery.html',
                           categories=categories,
                           photos=photos,
                           videos=videos,
                           form=form)


@dashboard_bp.route('/gallery/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_gallery_category(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    category = GalleryCategory.query.get_or_404(id)
    form = GalleryCategoryForm(obj=category)

    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        db.session.commit()
        flash('Gallery category updated successfully!', 'success')
        return redirect(url_for('dashboard.manage_gallery'))

    return render_template('dashboard/gallery_category_form.html', form=form, category=category, title='Edit Category')


@dashboard_bp.route('/gallery/items/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_gallery_item(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))


@main_bp.route('/check')
def check_app():
    """A simple diagnostic route to check if the Flask app is working"""
    return "App is running correctly"

    item = GalleryItem.query.get_or_404(id)
    form = GalleryItemForm(obj=item)
    form.category_id.choices = [(c.id, c.name) for c in GalleryCategory.query.all()]

    if form.validate_on_submit():
        item.title = form.title.data
        item.description = form.description.data
        item.category_id = form.category_id.data
        item.is_featured = form.is_featured.data

        if form.image.data:
            image = form.image.data
            filename = secure_filename(image.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'gallery', filename)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            image.save(image_path)
            item.image_url = f'/uploads/gallery/{filename}'

        db.session.commit()
        flash('Gallery item updated successfully!', 'success')
        return redirect(url_for('dashboard.manage_gallery'))

    return render_template('dashboard/gallery_item_form.html', form=form, item=item, title='Edit Gallery Item')


@dashboard_bp.route('/gallery/items/<int:id>/toggle')
@login_required
def toggle_gallery_item(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    item = GalleryItem.query.get_or_404(id)
    item.is_active = not item.is_active
    db.session.commit()

    status = "activated" if item.is_active else "deactivated"
    flash(f'Gallery item {status} successfully!', 'success')
    return redirect(url_for('dashboard.manage_gallery'))


@dashboard_bp.route('/gallery/items/<int:id>/delete', methods=['POST'])
@login_required
def delete_gallery_item(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    item = GalleryItem.query.get_or_404(id)

    try:
        # Debug log to track execution
        logger.info(f"Attempting to delete gallery item {id}: {item.title}")

        # Delete the file if it exists
        if item.image_url:
            # Handle both formats: with or without leading slash
            clean_path = item.image_url.lstrip('/')
            file_path = os.path.join(current_app.static_folder, clean_path)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted file: {file_path}")
                else:
                    logger.warning(f"File not found at path: {file_path}")
            except Exception as file_e:
                logger.error(f"Failed to delete file: {str(file_e)}")
                # Continue even if file deletion fails

        # Delete the database record
        db.session.delete(item)
        db.session.commit()
        flash('Gallery photo deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting gallery item: {str(e)}")
        flash(f'Error deleting gallery item: {str(e)}', 'danger')

    return redirect(url_for('dashboard.manage_gallery'))


@dashboard_bp.route('/media/<int:id>/toggle')
@login_required
def toggle_media(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    media = Media.query.get_or_404(id)
    media.is_featured = not media.is_featured
    db.session.commit()

    status = "featured" if media.is_featured else "unfeatured"
    flash(f'Media {status} successfully!', 'success')
    return redirect(url_for('dashboard.manage_gallery'))


@dashboard_bp.route('/media/<int:id>/delete', methods=['POST'])
@login_required
def delete_media(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    media = Media.query.get_or_404(id)

    try:
        # Debug log to track execution
        logger.info(f"Attempting to delete media {id}: {media.title}")

        # Only delete local files, not external links (YouTube, Facebook)
        if media.file_url and media.file_url.startswith('/uploads/') and not media.video_platform:
            try:
                file_path = os.path.join(current_app.static_folder, media.file_url.lstrip('/'))
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted file: {file_path}")
            except Exception as file_e:
                logger.error(f"Failed to delete media file: {str(file_e)}")
                # Continue even if file deletion fails

        # Delete thumbnail if exists
        if media.thumbnail_url and media.thumbnail_url.startswith('/uploads/'):
            try:
                thumb_path = os.path.join(current_app.static_folder, media.thumbnail_url.lstrip('/'))
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
                    logger.info(f"Deleted thumbnail: {thumb_path}")
            except Exception as thumb_e:
                logger.error(f"Failed to delete thumbnail: {str(thumb_e)}")
                # Continue even if thumbnail deletion fails

        db.session.delete(media)
        db.session.commit()
        flash('Media deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting media: {str(e)}")
        flash(f'Error deleting media: {str(e)}', 'danger')

    return redirect(url_for('dashboard.manage_gallery'))


@dashboard_bp.route('/disclosures/manage')
@login_required
def manage_disclosures():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    disclosures = PublicDisclosure.query.order_by(PublicDisclosure.category, PublicDisclosure.display_order).all()
    return render_template('dashboard/manage_disclosures.html', disclosures=disclosures)


@dashboard_bp.route('/disclosures/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_disclosure(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    disclosure = PublicDisclosure.query.get_or_404(id)
    form = PublicDisclosureForm(obj=disclosure)

    if form.validate_on_submit():
        disclosure.title = form.title.data
        disclosure.category = form.category.data
        disclosure.content = form.content.data
        disclosure.is_active = form.is_active.data
        disclosure.display_order = form.display_order.data

        if form.file.data:
            file = form.file.data
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'disclosures', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
            disclosure.file_url = f'/uploads/disclosures/{filename}'

        db.session.commit()
        flash('Public disclosure updated successfully!', 'success')
        return redirect(url_for('dashboard.manage_disclosures'))

    return render_template('dashboard/disclosure_form.html', form=form, disclosure=disclosure,
                           title='Edit Public Disclosure')


@dashboard_bp.route('/disclosures/<int:id>/toggle')
@login_required
def toggle_disclosure(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    disclosure = PublicDisclosure.query.get_or_404(id)
    disclosure.is_active = not disclosure.is_active
    db.session.commit()

    status = "activated" if disclosure.is_active else "deactivated"
    flash(f'Public disclosure {status} successfully!', 'success')
    return redirect(url_for('dashboard.manage_disclosures'))


@dashboard_bp.route('/popup-banners/manage')
@login_required
def manage_popup_banners():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    popups = PopupBanner.query.order_by(PopupBanner.created_at.desc()).all()
    return render_template('dashboard/manage_popup_banners.html', popups=popups)


@dashboard_bp.route('/popup-banners/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_popup_banner(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    popup = PopupBanner.query.get_or_404(id)
    form = PopupBannerForm(obj=popup)

    if form.validate_on_submit():
        popup.title = form.title.data
        popup.content = form.content.data
        popup.is_active = form.is_active.data
        popup.start_date = form.start_date.data
        popup.end_date = form.end_date.data

        if form.image.data:
            image = form.image.data
            filename = secure_filename(image.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'popups', filename)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            image.save(image_path)
            popup.image_url = f'/uploads/popups/{filename}'

        db.session.commit()
        flash('Popup banner updated successfully!', 'success')
        return redirect(url_for('dashboard.manage_popup_banners'))

    return render_template('dashboard/popup_banner_form.html', form=form, popup=popup, title='Edit Popup Banner')


@dashboard_bp.route('/popup-banners/<int:id>/toggle')
@login_required
def toggle_popup_banner(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    popup = PopupBanner.query.get_or_404(id)
    popup.is_active = not popup.is_active
    db.session.commit()

    status = "activated" if popup.is_active else "deactivated"
    flash(f'Popup banner {status} successfully!', 'success')
    return redirect(url_for('dashboard.manage_popup_banners'))


@dashboard_bp.route('/popup-banners/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_popup_banner(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    popup = PopupBanner.query.get_or_404(id)

    try:
        # Delete the image file if it exists
        if popup.image_url:
            image_path = os.path.join(current_app.static_folder, popup.image_url.lstrip('/'))
            if os.path.exists(image_path):
                os.remove(image_path)
                logger.info(f"Deleted popup image file: {image_path}")

        # Delete the database record
        db.session.delete(popup)
        db.session.commit()
        flash('Popup banner deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting popup banner: {str(e)}")
        flash(f'Error deleting popup banner: {str(e)}', 'danger')

    return redirect(url_for('dashboard.manage_popup_banners'))


@dashboard_bp.route('/documents/manage')
@login_required
def manage_documents():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    documents = Document.query.order_by(Document.created_at.desc()).all()
    return render_template('dashboard/manage_documents.html', documents=documents)


@dashboard_bp.route('/media/manage')
@login_required
def manage_media():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    media_items = Media.query.order_by(Media.created_at.desc()).all()
    return render_template('dashboard/manage_media.html', media_items=media_items)


# Gallery Routes
@dashboard_bp.route('/gallery/categories/new', methods=['GET', 'POST'])
@login_required
def new_gallery_category():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    form = GalleryCategoryForm()
    if form.validate_on_submit():
        category = GalleryCategory(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(category)
        db.session.commit()
        flash('Gallery category created successfully!', 'success')
        return redirect(url_for('dashboard.manage_gallery'))

    return render_template('dashboard/gallery_category_form.html', form=form, title='New Gallery Category')


@dashboard_bp.route('/gallery/items/new', methods=['GET', 'POST'])
@login_required
def new_gallery_item():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    form = GalleryItemForm()
    categories = GalleryCategory.query.all()

    if not categories:
        flash('Please create a gallery category first.', 'warning')
        return redirect(url_for('dashboard.new_gallery_category'))

    form.category_id.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        try:
            image = form.image.data
            filename = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{image.filename}")
            category = GalleryCategory.query.get(form.category_id.data)
            folder_name = secure_filename(category.name.lower().replace(' ', '_'))

            # Create folder with category name if it doesn't exist
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'gallery', folder_name, filename)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            image.save(image_path)

            item = GalleryItem(
                title=form.title.data,
                description=form.description.data,
                image_url=f'/uploads/gallery/{folder_name}/{filename}',
                category_id=form.category_id.data,
                is_featured=form.is_featured.data,
                is_active=form.is_active.data
            )
            db.session.add(item)
            db.session.commit()

            logger.info(f"Gallery item added: {item.image_url}")
            flash('Gallery item added successfully!', 'success')
            return redirect(url_for('dashboard.manage_gallery'))
        except Exception as e:
            logger.error(f"Error adding gallery item: {str(e)}")
            flash(f'Error adding gallery item: {str(e)}', 'danger')

    return render_template('dashboard/gallery_item_form.html', form=form, title='New Gallery Item')


# Fee Structure Routes
@dashboard_bp.route('/fee-structure/new', methods=['GET', 'POST'])
@login_required
def new_fee_structure():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    form = FeeStructureForm()
    if form.validate_on_submit():
        file_url = None
        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'fees', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
            file_url = f'/uploads/fees/{filename}'

        fee = FeeStructure(
            title=form.title.data,
            class_name=form.class_name.data if form.class_name.data else 'All Classes',
            fee_type=form.fee_type.data if form.fee_type.data else 'comprehensive',
            amount=form.amount.data if form.amount.data else 0.0,
            academic_year=form.academic_year.data,
            payment_frequency=form.payment_frequency.data if form.payment_frequency.data else 'annually',
            notes=form.notes.data,
            is_active=form.is_active.data,
            file_url=file_url
        )
        db.session.add(fee)
        db.session.commit()
        flash('Fee structure added successfully!', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('dashboard/fee_structure_form.html', form=form, title='New Fee Structure')


# Public Disclosure Routes
@dashboard_bp.route('/disclosures/new', methods=['GET', 'POST'])
@login_required
def new_disclosure():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    form = PublicDisclosureForm()
    if form.validate_on_submit():
        try:
            file_url = None
            if form.file.data:
                file = form.file.data
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'disclosures', filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                file.save(file_path)
                file_url = f'/uploads/disclosures/{filename}'

            disclosure = PublicDisclosure(
                title=form.title.data,
                category=form.category.data,
                content=form.content.data,
                file_url=file_url,
                is_active=form.is_active.data,
                display_order=form.display_order.data
            )
            db.session.add(disclosure)
            db.session.commit()
            flash('Public disclosure added successfully!', 'success')
            return redirect(url_for('dashboard.manage_disclosures'))
        except Exception as e:
            logger.error(f"Error adding disclosure: {str(e)}")
            flash('Error adding disclosure. Please try again.', 'danger')

    return render_template('dashboard/disclosure_form.html', form=form, title='New Public Disclosure')


# Frontend Routes for Gallery
@main_bp.route('/gallery/photos')
@main_bp.route('/gallery/photos/<int:category_id>')
def gallery_photos(category_id=None):
    categories = GalleryCategory.query.all()
    selected_category = GalleryCategory.query.get(category_id) if category_id else None

    if selected_category:
        photos = GalleryItem.query.filter_by(
            category_id=category_id,
            is_active=True
        ).order_by(GalleryItem.created_at.desc()).all()
    else:
        photos = GalleryItem.query.filter_by(is_active=True).order_by(GalleryItem.created_at.desc()).all()

    # Log image paths for debugging
    for photo in photos:
        logger.info(
            f"Photo path: {photo.image_url}, Exists: {os.path.exists(os.path.join(app.static_folder, photo.image_url.lstrip('/')))}")

    return render_template('gallery_photos.html',
                           categories=categories,
                           selected_category=selected_category,
                           photos=photos)


@main_bp.route('/gallery/videos')
@main_bp.route('/gallery/videos/<int:category_id>')
def gallery_videos(category_id=None):
    categories = GalleryCategory.query.all()
    selected_category = GalleryCategory.query.get(category_id) if category_id else None

    if selected_category:
        videos = Media.query.filter_by(
            gallery_category=selected_category.name,
            media_type='video',
            is_active=True
        ).order_by(Media.created_at.desc()).all()
    else:
        videos = Media.query.filter_by(
            media_type='video',
            is_active=True
        ).order_by(Media.created_at.desc()).all()

    return render_template('gallery_videos.html',
                           categories=categories,
                           selected_category=selected_category,
                           videos=videos)


# Public Disclosure Routes
@main_bp.route('/disclosure/<category>')
def disclosure(category):
    category_map = {
        'general': 'General Information',
        'documents': 'Documents & Information',
        'staff': 'Staff (Teaching)',
        'infrastructure': 'School Infrastructure',
        'results': 'Results & Academics'
    }

    category_title = category_map.get(category, 'Information')

    disclosures = PublicDisclosure.query.filter_by(
        category=category,
        is_active=True
    ).order_by(PublicDisclosure.display_order.asc()).all()

    return render_template('public_disclosure.html',
                           disclosures=disclosures,
                           category=category,
                           category_title=category_title)


# TC Retrieval Route
@main_bp.route('/tc-retrieval', methods=['GET', 'POST'])
def tc_retrieval():
    error = None
    tc = None

    if request.method == 'POST':
        admission_number = request.form.get('admission_number')

        # Try to find TC by admission number in the TC number pattern
        tc = TransferCertificate.query.filter(
            TransferCertificate.tc_number.like(f'TC-{admission_number}-%'),
            TransferCertificate.status == 'approved'
        ).order_by(TransferCertificate.created_at.desc()).first()

        # If not found by TC number pattern, try by student ID
        if not tc:
            # Find the user by admission number
            user = User.query.filter_by(username=admission_number).first()

            if user:
                # Look for TC by student ID
                tc = TransferCertificate.query.filter_by(
                    student_id=user.id,
                    status='approved'
                ).order_by(TransferCertificate.created_at.desc()).first()

        if not tc:
            error = "No approved Transfer Certificate found for this admission number."

    return render_template('tc_retrieval.html', tc=tc, error=error)


# Add a navbar item for TC retrieval in the main navbar
@app.context_processor
def inject_tc_retrieval_link():
    return dict(tc_retrieval_link=url_for('main.tc_retrieval'))


# Fee Structure Route
@main_bp.route('/fee-structure')
@main_bp.route('/fee-structure/<academic_year>')
def fee_structure(academic_year=None):
    # Get all unique academic years
    academic_years = db.session.query(FeeStructure.academic_year).filter_by(
        is_active=True
    ).distinct().order_by(FeeStructure.academic_year.desc()).all()
    academic_years = [year[0] for year in academic_years]

    # If no academic year specified, use the most recent one
    if not academic_year and academic_years:
        academic_year = academic_years[0]

    # Get fees for the selected academic year
    fees = FeeStructure.query.filter_by(
        academic_year=academic_year,
        is_active=True
    ).order_by(FeeStructure.class_name, FeeStructure.fee_type).all()

    return render_template('fee_structure.html',
                           fees=fees,
                           academic_years=academic_years,
                           selected_year=academic_year)


@dashboard_bp.route('/tc/upload/<int:tc_id>', methods=['GET', 'POST'])
@login_required
def admin_upload_tc(tc_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    # Get the existing TC request
    tc = TransferCertificate.query.get_or_404(tc_id)
    student = User.query.get_or_404(tc.student_id)

    if request.method == 'POST':
        try:
            tc_file = request.files.get('tc_file')

            if tc_file:
                filename = secure_filename(
                    f"TC-{student.username}-{datetime.utcnow().strftime('%Y%m%d%H%M')}.{tc_file.filename.split('.')[-1]}")
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'tc', filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                tc_file.save(file_path)

                # Update the existing TC record
                tc.status = 'approved'
                tc.file_url = f'/uploads/tc/{filename}'
                db.session.commit()

                flash('Transfer Certificate uploaded successfully!', 'success')
                return redirect(url_for('dashboard.manage_tc'))
            else:
                flash('No file selected', 'danger')
        except Exception as e:
            logger.error(f"Error uploading TC: {str(e)}")
            flash(f'Error uploading TC: {str(e)}', 'danger')

    return render_template('dashboard/upload_tc.html', tc=tc, student=student)


# Route to directly upload a new TC without a request
@dashboard_bp.route('/tc/new', methods=['GET', 'POST'])
@login_required
def new_tc():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        try:
            admission_number = request.form.get('admission_number')
            reason = request.form.get('reason')
            tc_file = request.files.get('tc_file')

            if tc_file and admission_number:
                # Find student if exists, but don't require it
                student = User.query.filter_by(username=admission_number).first()

                # Generate a timestamp for the TC
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M')

                # Create a secure filename
                filename = secure_filename(
                    f"TC-{admission_number}-{timestamp}.{tc_file.filename.split('.')[-1]}")
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'tc', filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                tc_file.save(file_path)

                # Create TC record
                tc = TransferCertificate(
                    student_id=student.id if student else None,
                    reason=reason if reason else "Issued by administrator",
                    tc_number=f'TC-{admission_number}-{timestamp}',
                    status='approved',
                    file_url=f'/uploads/tc/{filename}'
                )
                db.session.add(tc)
                db.session.commit()
                flash('Transfer Certificate created and uploaded successfully!', 'success')
                return redirect(url_for('dashboard.manage_tc'))
            else:
                flash('Admission number and TC file are required', 'danger')
        except Exception as e:
            logger.error(f"Error creating TC: {str(e)}")
            flash(f'Error creating TC: {str(e)}', 'danger')

    return render_template('dashboard/new_tc.html')


# Registration Code Management
@dashboard_bp.route('/registration-codes')
@login_required
def manage_registration_codes():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    from models import Teacher
    codes = RegistrationCode.query.order_by(RegistrationCode.created_at.desc()).all()
    return render_template('dashboard/registration_codes.html', codes=codes, User=User, Teacher=Teacher)


@dashboard_bp.route('/registration-codes/delete/<int:id>')
@login_required
def delete_registration_code(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    code = RegistrationCode.query.get_or_404(id)
    if code.is_used:
        flash('Cannot delete a code that has already been used.', 'danger')
    else:
        db.session.delete(code)
        db.session.commit()
        flash('Registration code deleted successfully.', 'success')

    return redirect(url_for('dashboard.manage_registration_codes'))


@dashboard_bp.route('/registration-codes/generate', methods=['GET', 'POST'])
@login_required
def generate_registration_code():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    form = RegistrationCodeForm()
    if form.validate_on_submit():
        import random
        import string

        # Generate a random code
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

        # Create a new registration code
        reg_code = RegistrationCode(
            code=code,
            role=form.role.data,
            is_used=False
        )

        db.session.add(reg_code)
        db.session.commit()

        flash(f'Registration code generated: {code}', 'success')
        return redirect(url_for('dashboard.manage_registration_codes'))

    # Fetch recent codes for display
    codes = RegistrationCode.query.order_by(RegistrationCode.created_at.desc()).limit(5).all()
    return render_template('dashboard/generate_code.html', form=form, codes=codes, User=User)


# Admin Contact Message Management
@dashboard_bp.route('/tc/manage')
@login_required
def manage_tc():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    # Get all TC requests, ordered by creation date (newest first)
    transfer_certificates = TransferCertificate.query.order_by(TransferCertificate.created_at.desc()).all()

    # Get user information for each TC
    for tc in transfer_certificates:
        tc.student = User.query.get(tc.student_id)

    return render_template('dashboard/manage_tc.html', transfer_certificates=transfer_certificates)


@dashboard_bp.route('/messages')
@login_required
def manage_messages():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('dashboard/messages.html', messages=messages)


@dashboard_bp.route('/messages/<int:id>/respond', methods=['GET', 'POST'])
@login_required
def respond_message(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    message = ContactMessage.query.get_or_404(id)
    form = ContactResponseForm()

    if form.validate_on_submit():
        message.response = form.response.data
        message.status = 'responded'
        message.responded_at = datetime.utcnow()
        message.responded_by = current_user.id
        db.session.commit()
        flash('Response sent successfully!', 'success')
        return redirect(url_for('dashboard.manage_messages'))

    return render_template('dashboard/message_response.html', form=form, message=message)


# Student Dashboard Routes
@dashboard_bp.route('/attendance/view')
@login_required
def view_attendance():
    if current_user.role != 'student':
        flash('Access denied. Student privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    attendances = Attendance.query.filter_by(student_id=current_user.id).order_by(Attendance.date.desc()).all()
    return render_template('dashboard/view_attendance.html', attendances=attendances)


@dashboard_bp.route('/assignments')
@login_required
def student_assignments():
    if current_user.role != 'student':
        flash('Access denied. Student privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    assignments = Assignment.query.filter_by(student_id=current_user.id).order_by(Assignment.due_date.desc()).all()
    return render_template('dashboard/student_assignments.html', assignments=assignments)


@dashboard_bp.route('/tc/my')
@login_required
def my_tc():
    if current_user.role != 'student':
        flash('Access denied. Student privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    tcs = TransferCertificate.query.filter_by(student_id=current_user.id).order_by(
        TransferCertificate.created_at.desc()).all()

    return render_template('dashboard/my_tc.html', tcs=tcs)


# User Management Routes
@dashboard_bp.route('/users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    users = User.query.order_by(User.created_at.desc()).all()
    teachers = Teacher.query.order_by(Teacher.created_at.desc()).all()
    return render_template('dashboard/manage_users.html', users=users, teachers=teachers)


@dashboard_bp.route('/users/<int:id>/reset-password', methods=['GET', 'POST'])
@login_required
def reset_user_password(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(id)

    if request.method == 'POST':
        # Generate a random password
        import random
        import string
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        user.set_password(new_password)
        db.session.commit()

        flash(f'Password for {user.username} has been reset to: {new_password}', 'success')
        return redirect(url_for('dashboard.manage_users'))

    # GET request - show confirmation page
    return render_template('dashboard/admin_change_user_password.html', user=user, form=PasswordChangeForm())


@dashboard_bp.route('/users/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_user(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    if current_user.id == id:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('dashboard.manage_users'))

    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()

    flash(f'User {user.username} has been deleted.', 'success')
    return redirect(url_for('dashboard.manage_users'))


@dashboard_bp.route('/teachers/<int:id>/reset-password', methods=['GET', 'POST'])
@login_required
def reset_teacher_password(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    teacher = Teacher.query.get_or_404(id)

    if request.method == 'POST':
        # Generate a random password
        import random
        import string
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        teacher.set_password(new_password)
        db.session.commit()

        flash(f'Password for {teacher.username} has been reset to: {new_password}', 'success')
        return redirect(url_for('dashboard.manage_users'))

    # GET request - show confirmation page
    return render_template('dashboard/admin_change_user_password.html', user=teacher, form=PasswordChangeForm())


@dashboard_bp.route('/teachers/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_teacher(id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('dashboard.index'))

    teacher = Teacher.query.get_or_404(id)
    db.session.delete(teacher)
    db.session.commit()

    flash(f'Teacher {teacher.username} has been deleted.', 'success')
    return redirect(url_for('dashboard.manage_users'))


@dashboard_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = PasswordChangeForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Current password is incorrect!', 'danger')
    return render_template('dashboard/change_password.html', form=form)