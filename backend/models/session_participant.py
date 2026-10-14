"""
SessionParticipant model representing the 'session_participants' table in MySQL.
Allows multiple mentees from the same domain to participate in one mentorship session.
"""

from datetime import datetime, timezone
from extensions import db


class SessionParticipant(db.Model):
    """
    Association table tracking multiple mentee participants in a Session.
    Enforces that mentees participating in a session are from the same domain.
    """
    __tablename__ = 'session_participants'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    mentee_id = db.Column(db.Integer, db.ForeignKey('mentee_profiles.id', ondelete='CASCADE'), nullable=False)
    joined_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('session_id', 'mentee_id', name='uq_session_participant'),
    )

    session = db.relationship('Session', backref=db.backref('participants', lazy=True, cascade='all, delete-orphan'))
    mentee = db.relationship('MenteeProfile', backref=db.backref('session_participations', lazy=True, cascade='all, delete-orphan'))

    def __init__(self, **kwargs):
        kwargs.setdefault('joined_at', datetime.now(timezone.utc))
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<SessionParticipant session_id={self.session_id} mentee_id={self.mentee_id}>"
