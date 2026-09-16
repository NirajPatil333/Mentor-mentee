"""
Achievement model representing the 'achievements' table in MySQL.
Stores milestone achievements, awards, and recognitions earned by mentees.
"""

from datetime import datetime, timezone
from extensions import db


class Achievement(db.Model):
    """
    Stores achievements, awards, project milestones, and recognitions for mentees.
    Linked to MenteeProfile via mentee_id.
    """
    __tablename__ = 'achievements'

    # Primary key, auto-incrementing integer
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign key referencing the mentee_profiles table
    mentee_id = db.Column(db.Integer, db.ForeignKey('mentee_profiles.id'), nullable=False)

    # Achievement title/headline
    title = db.Column(db.String(200), nullable=False)

    # Optional description detailing the achievement
    description = db.Column(db.Text, nullable=True)

    # Date when the achievement was attained
    achievement_date = db.Column(db.Date, nullable=False)

    # Optional link or proof URL (e.g. project URL, verification badge, publication link)
    achievement_url = db.Column(db.String(500), nullable=True)

    # Timezone-aware UTC timestamp
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationship to access the associated MenteeProfile model
    mentee = db.relationship('MenteeProfile', backref=db.backref('achievements', lazy=True))

    def __init__(self, **kwargs):
        kwargs.setdefault('created_at', datetime.now(timezone.utc))
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Achievement id={self.id} mentee_id={self.mentee_id} title='{self.title}'>"
