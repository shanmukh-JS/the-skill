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

class DevelopmentConfig(Config):
    DEBUG = True
    db_url = os.environ.get('DATABASE_URL') or f"sqlite:///{basedir / 'app.db'}"
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = db_url

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
    
    db_url = os.environ.get('DATABASE_URL') or f"sqlite:///{basedir / 'app.db'}"
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = db_url

    @classmethod
    def init_app(cls, app):
        secret = os.environ.get('SECRET_KEY')
        if not secret or secret == 'dev-secret-key-fallback-change-in-prod':
            app.logger.warning("ProductionConfig: SECRET_KEY not explicitly set; using fallback secret key.")

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
