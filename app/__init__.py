from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from .config import BaseConfig

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[BaseConfig.RATELIMIT_DEFAULT],
    storage_uri='memory://'
)

def create_app(config_overrides=None):
    app = Flask(__name__)
    app.config.from_object(BaseConfig)
    if config_overrides:
        app.config.update(config_overrides)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    # Login Manager Settings
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Import models here to avoid circular imports
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return None

    # Import and register Blueprints
    from app.auth.routes import auth
    from app.blog.routes import blog

    app.register_blueprint(auth)
    app.register_blueprint(blog)

    # Create database tables if not already created
    if not app.config.get('TESTING'):
        with app.app_context():
            db.create_all()
            uploads_path = app.config['UPLOAD_FOLDER']
            import os
            os.makedirs(uploads_path, exist_ok=True)

    return app
