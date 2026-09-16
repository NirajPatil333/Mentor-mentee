"""
Progress model representing the 'progress' table in MySQL.
Tracks learning goals and milestone achievements for mentees with optional mentor oversight.
"""

from datetime import datetime, timezone
from extensions import db


class Progress(db.Model):
    """
    Stores individual learning goals, description, progress percentage (0-100),
    status, and links to MenteeProfile, MentorProfile, and Skill.
    Enforces a database-level CHECK constraint on progress_percentage.
    """
    __tablename__ = 'progress'

    # Primary key, auto-incrementing integer
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign key referencing the mentee_profiles table
    mentee_id = db.Column(db.Integer, db.ForeignKey('mentee_profiles.id'), nullable=False)

    # Optional foreign key referencing the mentor_profiles table (mentoring guide)
    mentor_id = db.Column(db.Integer, db.ForeignKey('mentor_profiles.id'), nullable=True)

    # Foreign key referencing the skills table (skill being developed)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)

    # Goal title/summary and detailed description
    goal = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Progress completion percentage (0 - 100)
    progress_percentage = db.Column(db.Integer, nullable=False, default=0, server_default='0')

    # Current goal status (e.g. 'not_started', 'in_progress', 'completed')
    status = db.Column(db.String(30), nullable=False, default='not_started', server_default='not_started')

    # Timezone-aware UTC timestamp
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Table constraints: check constraint ensuring progress_percentage is between 0 and 100
    __table_args__ = (
        db.CheckConstraint(
            'progress_percentage >= 0 AND progress_percentage <= 100',
            name='ck_progress_percentage_range'
        ),
    )

    # Relationships to access associated MenteeProfile, MentorProfile, and Skill models
    mentee = db.relationship('MenteeProfile', backref=db.backref('progress_records', lazy=True))
    mentor = db.relationship('MentorProfile', backref=db.backref('progress_records', lazy=True))
    skill = db.relationship('Skill', backref=db.backref('progress_records', lazy=True))

    def __init__(self, **kwargs):
        kwargs.setdefault('progress_percentage', 0)
        kwargs.setdefault('status', 'not_started')
        kwargs.setdefault('updated_at', datetime.now(timezone.utc))
        super().__init__(**kwargs)

    def __repr__(self):
        return (
            f"<Progress id={self.id} mentee_id={self.mentee_id} "
            f"skill_id={self.skill_id} progress={self.progress_percentage}% status='{self.status}'>"
        )
