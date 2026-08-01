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
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{basedir / 'app.db'}"

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
    
    @classmethod
    def init_app(cls, app):
        secret = os.environ.get('SECRET_KEY')
        if not secret or secret == 'dev-secret-key-fallback-change-in-prod':
            raise ValueError("CRITICAL SECURITY RISK: ProductionConfig selected but SECRET_KEY environment variable is missing or insecure!")
        
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            raise ValueError("CRITICAL CONFIGURATION ERROR: ProductionConfig selected but DATABASE_URL is missing!")

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
