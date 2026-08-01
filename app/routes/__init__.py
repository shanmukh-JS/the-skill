from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.profile import profile_bp
from app.routes.skills import skills_bp
from app.routes.search import search_bp
from app.routes.requests import requests_bp
from app.routes.chat import chat_bp
from app.routes.ratings import ratings_bp
from app.routes.dashboard import dashboard_bp
from app.routes.admin import admin_bp

__all__ = [
    'main_bp',
    'auth_bp',
    'profile_bp',
    'skills_bp',
    'search_bp',
    'requests_bp',
    'chat_bp',
    'ratings_bp',
    'dashboard_bp',
    'admin_bp'
]
