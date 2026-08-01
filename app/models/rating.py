from datetime import datetime, timezone
from app.extensions import db

class Rating(db.Model):
    __tablename__ = 'ratings'
    __table_args__ = (
        db.UniqueConstraint('request_id', 'rater_id', name='uq_rating_request_rater'),
        db.CheckConstraint('score >= 1 AND score <= 5', name='ck_rating_score_range'),
    )

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id', ondelete='CASCADE'), nullable=False)
    rater_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rated_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def is_editable(self):
        # 24-hour edit window check
        elapsed = datetime.now(timezone.utc) - self.created_at.replace(tzinfo=timezone.utc) if self.created_at.tzinfo is None else datetime.now(timezone.utc) - self.created_at
        return elapsed.total_seconds() <= 86400

    def __repr__(self):
        return f'<Rating #{self.id} score={self.score} for User {self.rated_user_id} by User {self.rater_id}>'
