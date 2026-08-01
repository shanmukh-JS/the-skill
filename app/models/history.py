from datetime import datetime, timezone
from app.extensions import db

class LearningHistory(db.Model):
    __tablename__ = 'learning_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # teacher, learner
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id', ondelete='CASCADE'), nullable=False)
    completed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    request_obj = db.relationship('Request', foreign_keys=[request_id])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<LearningHistory User {self.user_id} as {self.role} for Skill {self.skill_id}>'
