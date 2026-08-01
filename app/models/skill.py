from datetime import datetime, timezone
from app.extensions import db

class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    proficiency_level = db.Column(db.String(20), nullable=False)  # Beginner, Intermediate, Advanced, Expert
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # Soft delete flag
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    requests = db.relationship('Request', backref='skill', lazy='dynamic')
    learning_records = db.relationship('LearningHistory', backref='skill', lazy='dynamic')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Skill {self.name} ({self.proficiency_level}) by User {self.user_id}>'


class LearningInterest(db.Model):
    __tablename__ = 'learning_interests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<LearningInterest {self.skill_name} for User {self.user_id}>'
