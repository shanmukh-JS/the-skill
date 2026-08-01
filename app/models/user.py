from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from app.extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True, default='default_avatar.png')
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    skills = db.relationship('Skill', backref='teacher', lazy='dynamic', cascade='all, delete-orphan')
    learning_interests = db.relationship('LearningInterest', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    sent_requests = db.relationship('Request', foreign_keys='Request.sender_id', backref='sender', lazy='dynamic')
    received_requests = db.relationship('Request', foreign_keys='Request.receiver_id', backref='receiver', lazy='dynamic')
    ratings_given = db.relationship('Rating', foreign_keys='Rating.rater_id', backref='rater', lazy='dynamic')
    ratings_received = db.relationship('Rating', foreign_keys='Rating.rated_user_id', backref='rated_user', lazy='dynamic')
    learning_records = db.relationship('LearningHistory', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def average_rating(self):
        from app.models.rating import Rating
        if 'ratings_received' in self.__dict__ and isinstance(self.__dict__['ratings_received'], list):
            scores = [r.score for r in self.ratings_received]
            return round(sum(scores) / len(scores), 1) if scores else 0.0
        avg_score = db.session.query(func.avg(Rating.score)).filter(Rating.rated_user_id == self.id).scalar()
        return round(float(avg_score), 1) if avg_score is not None else 0.0

    def rating_count(self):
        from app.models.rating import Rating
        if 'ratings_received' in self.__dict__ and isinstance(self.__dict__['ratings_received'], list):
            return len(self.ratings_received)
        return Rating.query.filter_by(rated_user_id=self.id).count()

    def completed_teaching_count(self):
        from app.models.history import LearningHistory
        return LearningHistory.query.filter_by(user_id=self.id, role='teacher').count()

    def completed_learning_count(self):
        from app.models.history import LearningHistory
        return LearningHistory.query.filter_by(user_id=self.id, role='learner').count()

    def unread_notification_count(self):
        from app.models.notification import Notification
        return Notification.query.filter_by(user_id=self.id, is_read=False).count()

    def get_id(self):
        import hashlib
        pass_sig = hashlib.sha256(self.password_hash.encode('utf-8')).hexdigest()[:8]
        return f"{self.id}:{pass_sig}"

    def __repr__(self):
        return f'<User {self.username}>'


class FailedLogin(db.Model):
    __tablename__ = 'failed_logins'

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    username = db.Column(db.String(80), nullable=False, index=True)
    attempted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<FailedLogin {self.username} from {self.ip_address} at {self.attempted_at}>'
