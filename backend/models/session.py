"""
Session model representing the 'sessions' table in MySQL.
Manages scheduled mentoring sessions between mentors and mentees.
"""

from datetime import datetime, timezone
from extensions import db


class Session(db.Model):
    """
    Stores scheduled mentoring session details, including scheduling information,
    meeting room references, and links to the associated MentorshipRequest,
    MentorProfile, and MenteeProfile.
    """
    __tablename__ = 'sessions'

    # Primary key, auto-incrementing integer
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign key referencing the mentorship_requests table
    request_id = db.Column(db.Integer, db.ForeignKey('mentorship_requests.id'), nullable=False)

    # Foreign key referencing the mentor_profiles table
    mentor_id = db.Column(db.Integer, db.ForeignKey('mentor_profiles.id'), nullable=False)

    # Foreign key referencing the mentee_profiles table
    mentee_id = db.Column(db.Integer, db.ForeignKey('mentee_profiles.id'), nullable=False)

    # Session details
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Date and time window
    scheduled_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    # Video meeting room reference (storage only)
    meeting_room = db.Column(db.String(255), nullable=True)

    # Session status with default 'scheduled'
    status = db.Column(db.String(20), nullable=False, default='scheduled', server_default='scheduled')

    # Timezone-aware UTC creation timestamp
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships to access associated MentorshipRequest, MentorProfile, and MenteeProfile
    request = db.relationship('MentorshipRequest', backref=db.backref('sessions', lazy=True))
    mentor = db.relationship('MentorProfile', backref=db.backref('sessions', lazy=True))
    mentee = db.relationship('MenteeProfile', backref=db.backref('sessions', lazy=True))

    def __init__(self, **kwargs):
        kwargs.setdefault('status', 'scheduled')
        kwargs.setdefault('created_at', datetime.now(timezone.utc))
        super().__init__(**kwargs)

    def __repr__(self):
        return (
            f"<Session id={self.id} title='{self.title}' "
            f"date={self.scheduled_date} {self.start_time}-{self.end_time} status='{self.status}'>"
        )
