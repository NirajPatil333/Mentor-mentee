"""
Feedback model representing the 'feedback' table in MySQL.
Stores ratings and comments provided by mentees after mentoring sessions.
"""

from datetime import datetime, timezone
from extensions import db


class Feedback(db.Model):
    """
    Stores session feedback and star ratings (1-5) submitted by mentees for mentors.
    Enforces constraints:
    - CHECK constraint on rating (1 to 5)
    - UNIQUE constraint on (session_id, mentee_id) to ensure single feedback per session
    """
    __tablename__ = 'feedback'

    # Primary key, auto-incrementing integer
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign key referencing the sessions table
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)

    # Foreign key referencing the mentor_profiles table
    mentor_id = db.Column(db.Integer, db.ForeignKey('mentor_profiles.id'), nullable=False)

    # Foreign key referencing the mentee_profiles table
    mentee_id = db.Column(db.Integer, db.ForeignKey('mentee_profiles.id'), nullable=False)

    # Rating integer (1 to 5)
    rating = db.Column(db.Integer, nullable=False)

    # Optional feedback comment/review
    comment = db.Column(db.Text, nullable=True)

    # Timezone-aware UTC timestamp
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Table constraints:
    # 1. Rating check between 1 and 5
    # 2. Composite unique on session_id and mentee_id
    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_feedback_rating_range'),
        db.UniqueConstraint('session_id', 'mentee_id', name='uq_feedback_session_mentee'),
    )

    # Relationships to access associated Session, MentorProfile, and MenteeProfile models
    session = db.relationship('Session', backref=db.backref('feedbacks', lazy=True))
    mentor = db.relationship('MentorProfile', backref=db.backref('feedbacks', lazy=True))
    mentee = db.relationship('MenteeProfile', backref=db.backref('feedbacks', lazy=True))

    def __init__(self, **kwargs):
        kwargs.setdefault('created_at', datetime.now(timezone.utc))
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Feedback id={self.id} session_id={self.session_id} rating={self.rating}>"
