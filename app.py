import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "default-dev-key")  # Fallback for development
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schoolhub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = True  # Enable CSRF protection

# Ensure instance folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
logger.info(f"Instance path: {app.instance_path}")

# Configure database

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)
login_manager.login_view = 'auth.login'


# Add csrf_token to all templates
@app.context_processor
def inject_csrf_token():
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=generate_csrf)


# Import routes after app creation to avoid circular imports
with app.app_context():
    from routes import register_blueprints

    register_blueprints(app)

    # Log registered routes
    logger.info("Registered routes:")
    for rule in app.url_map.iter_rules():
        logger.info(f"Route: {rule.rule} [{', '.join(rule.methods)}] -> {rule.endpoint}")

    # Import models and create tables
    import models

    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")


# Add logging for the user_loader function
@login_manager.user_loader
def load_user(id):
    from flask import session

    # Check if we have a user_type in session to help determine the correct model
    user_type = session.get('user_type')

    if user_type == 'teacher':
        # Load teacher directly if we know it's a teacher
        from models import Teacher
        teacher = Teacher.query.get(int(id))
        if teacher:
            logger.info(f"Loaded Teacher: {teacher.username}, ID: {id}, Type: {type(teacher).__name__}")
            return teacher
    elif user_type == 'user':
        # Load user directly if we know it's a regular user
        from models import User
        user = User.query.get(int(id))
        if user:
            logger.info(f"Loaded User: {user.username}, ID: {id}, Type: {type(user).__name__}")
            return user
    else:
        # Fallback to the original behavior if session doesn't have user_type
        # Try to load a user first
        from models import User, Teacher

        # Check if the ID matches a Teacher first
        teacher = Teacher.query.get(int(id))
        if teacher:
            logger.info(f"Loaded Teacher (fallback): {teacher.username}, ID: {id}, Type: {type(teacher).__name__}")
            return teacher

        # Then check if it's a User
        user = User.query.get(int(id))
        if user:
            logger.info(f"Loaded User (fallback): {user.username}, ID: {id}, Type: {type(user).__name__}")
            return user

    return None


# Add after existing routes

# Import needed at the top of the file
from datetime import datetime
from flask import render_template
from models import PopupBanner  # Make sure this import exists


# Add this to your home route or main route
@app.route('/')
def home():
    # Get any active popup banners
    show_popup = False
    popup = None

    current_date = datetime.now().date()
    active_popup = PopupBanner.query.filter_by(is_active=True).first()

    if active_popup:
        # Check if popup is within valid date range if dates are set
        date_valid = True
        if active_popup.start_date and active_popup.start_date > current_date:
            date_valid = False
        if active_popup.end_date and active_popup.end_date < current_date:
            date_valid = False

        if date_valid:
            show_popup = True
            popup = active_popup

    # Get any other data needed for your home page
    # ...

    return render_template('home.html', show_popup=show_popup, popup=popup)