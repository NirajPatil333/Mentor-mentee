"""
MentorshipRequest model representing the 'mentorship_requests' table in MySQL.
Manages mentorship requests initiated by mentees to prospective mentors.
"""

from datetime import datetime, timezone
from extensions import db


class MentorshipRequest(db.Model):
    """
    Stores mentorship requests sent from a MenteeProfile to a MentorProfile.
    Tracks status (e.g. 'pending', 'accepted', 'rejected') and timestamps.
    """
    __tablename__ = 'mentorship_requests'

    # Primary key, auto-incrementing integer
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign key referencing the mentee_profiles table
    mentee_id = db.Column(db.Integer, db.ForeignKey('mentee_profiles.id'), nullable=False)

    # Foreign key referencing the mentor_profiles table
    mentor_id = db.Column(db.Integer, db.ForeignKey('mentor_profiles.id'), nullable=False)

    # Optional introductory message from the mentee
    message = db.Column(db.Text, nullable=True)

    # Current request status with default 'pending'
    status = db.Column(db.String(20), nullable=False, default='pending', server_default='pending')

    # Timezone-aware UTC timestamps
    requested_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    responded_at = db.Column(db.DateTime, nullable=True)

    # Relationships to access associated MenteeProfile and MentorProfile models
    mentee = db.relationship('MenteeProfile', backref=db.backref('mentorship_requests', lazy=True))
    mentor = db.relationship('MentorProfile', backref=db.backref('mentorship_requests', lazy=True))

    def __init__(self, **kwargs):
        kwargs.setdefault('status', 'pending')
        kwargs.setdefault('requested_at', datetime.now(timezone.utc))
        super().__init__(**kwargs)

    def __repr__(self):
        return (
            f"<MentorshipRequest id={self.id} mentee_id={self.mentee_id} "
            f"mentor_id={self.mentor_id} status='{self.status}'>"
        )
