"""
Resource model representing the 'resources' table in MySQL.
Stores educational materials, links, and documents shared by mentors with mentees.
"""

from datetime import datetime, timezone
from extensions import db


class Resource(db.Model):
    """
    Stores shared resources such as articles, documents, code repositories, or links.
    Always associated with a MentorProfile (creator/uploader), and optionally scoped
    to a specific MenteeProfile (or public/general when mentee_id is None).
    """
    __tablename__ = 'resources'

    # Primary key, auto-incrementing integer
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign key referencing the mentor_profiles table (resource creator)
    mentor_id = db.Column(db.Integer, db.ForeignKey('mentor_profiles.id'), nullable=False)

    # Optional foreign key referencing the mentee_profiles table (target recipient, or None if public/general)
    mentee_id = db.Column(db.Integer, db.ForeignKey('mentee_profiles.id'), nullable=True)

    # Resource details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    resource_type = db.Column(db.String(50), nullable=False)

    # External link or file storage path
    resource_url = db.Column(db.String(500), nullable=True)
    file_path = db.Column(db.String(500), nullable=True)

    # Timezone-aware UTC creation timestamp
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships to access associated MentorProfile and MenteeProfile models
    mentor = db.relationship('MentorProfile', backref=db.backref('resources', lazy=True))
    mentee = db.relationship('MenteeProfile', backref=db.backref('resources', lazy=True))

    def __init__(self, **kwargs):
        kwargs.setdefault('created_at', datetime.now(timezone.utc))
        super().__init__(**kwargs)

    def __repr__(self):
        return (
            f"<Resource id={self.id} title='{self.title}' "
            f"type='{self.resource_type}' mentor_id={self.mentor_id}>"
        )
