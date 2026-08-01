import os
from flask import Flask
from app.config import config
from app.extensions import db, login_manager, csrf, migrate

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app_config = config[config_name]
    app.config.from_object(app_config)
    
    if hasattr(app_config, 'init_app'):
        app_config.init_app(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # User loader callback (supporting multi-device session invalidation)
    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        if not user_id:
            return None
        if ':' in str(user_id):
            uid, pass_sig = str(user_id).split(':', 1)
            user = db.session.get(User, int(uid))
            if user:
                import hashlib
                current_sig = hashlib.sha256(user.password_hash.encode('utf-8')).hexdigest()[:8]
                if current_sig == pass_sig:
                    return user
            return None
        try:
            return db.session.get(User, int(user_id))
        except (ValueError, TypeError):
            return None

    # Register blueprints (all 10)
    from app.routes import (
        main_bp, auth_bp, profile_bp, skills_bp, search_bp,
        requests_bp, chat_bp, ratings_bp, dashboard_bp, admin_bp
    )
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(skills_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(ratings_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)

    # Global context processors for templates
    @app.context_processor
    def inject_global_vars():
        from flask_login import current_user
        from app.models.notification import Notification
        if current_user.is_authenticated:
            return {
                'unread_notif_count': current_user.unread_notification_count(),
                'recent_notifications': Notification.query
                    .filter_by(user_id=current_user.id)
                    .order_by(Notification.created_at.desc())
                    .limit(5).all()
            }
        return {'unread_notif_count': 0, 'recent_notifications': []}

    # Security response headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        return response

    # Error handlers
    from flask import render_template
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('main/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('main/500.html'), 500

    return app
