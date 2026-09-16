"""
Certificate model representing the 'certificates' table in MySQL.
Stores records of certificates awarded to mentees upon completing mentorship milestones.
"""

from datetime import datetime, timezone
from extensions import db


class Certificate(db.Model):
    """
    Stores certificate metadata for mentees including title, issuer, issue date,
    and storage path references for downloaded/generated certificates.
    """
    __tablename__ = 'certificates'

    # Primary key, auto-incrementing integer
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign key referencing the mentee_profiles table
    mentee_id = db.Column(db.Integer, db.ForeignKey('mentee_profiles.id'), nullable=False)

    # Certificate details
    title = db.Column(db.String(200), nullable=False)
    issuer = db.Column(db.String(200), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)

    # File storage reference (paths only; binaries are not stored directly in MySQL)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)

    # Timezone-aware UTC timestamp
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationship to access the associated MenteeProfile model
    mentee = db.relationship('MenteeProfile', backref=db.backref('certificates', lazy=True))

    def __init__(self, **kwargs):
        kwargs.setdefault('created_at', datetime.now(timezone.utc))
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Certificate id={self.id} mentee_id={self.mentee_id} title='{self.title}'>"
