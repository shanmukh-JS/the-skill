import os
from pathlib import Path
from dotenv import load_dotenv

basedir = Path(__file__).resolve().parent.parent
load_dotenv(basedir / '.env')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-fallback-change-in-prod')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads configuration
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB max file size
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads', 'profile_pics')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    # Cookie security defaults
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Mail Server Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME', 'noreply@skillexchange.org'))

def format_db_url(db_url):
    if not db_url:
        return f"sqlite:///{basedir / 'app.db'}"
    if db_url.startswith("postgres://"):
        return db_url.replace("postgres://", "postgresql+pg8000://", 1)
    if db_url.startswith("postgresql://") and "+pg8000" not in db_url:
        return db_url.replace("postgresql://", "postgresql+pg8000://", 1)
    return db_url

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = format_db_url(os.environ.get('DATABASE_URL'))

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False  # Simplify form submission testing while keeping full validation
    UPLOAD_FOLDER = os.path.join(basedir, 'tests', 'test_uploads')

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_DATABASE_URI = format_db_url(os.environ.get('DATABASE_URL'))

    @classmethod
    def init_app(cls, app):
        secret = os.environ.get('SECRET_KEY')
        if not secret or secret == 'dev-secret-key-fallback-change-in-prod':
            raise ValueError(
                "CRITICAL SECURITY ERROR: SECRET_KEY environment variable MUST be explicitly set "
                "in ProductionConfig! Refusing to run production server with insecure fallback secret."
            )

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
