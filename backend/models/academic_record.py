"""
AcademicRecord model representing the 'academic_records' table in MySQL.
Stores semester-wise SGPA, marksheet documents, and mentor verification status.
"""

from datetime import datetime, timezone
from extensions import db


class AcademicRecord(db.Model):
    """
    Stores mentee semester performance (SGPA), uploaded marksheet files,
    and mentor verification metadata.
    Enforces a unique constraint on (mentee_id, semester) to prevent duplicate semesters.
    """
    __tablename__ = 'academic_records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign key referencing mentee_profiles table
    mentee_id = db.Column(
        db.Integer,
        db.ForeignKey('mentee_profiles.id', ondelete='CASCADE'),
        nullable=False
    )

    # Semester number (e.g. 1, 2, 3...)
    semester = db.Column(db.Integer, nullable=False)

    # Semester Grade Point Average (0.00 to 10.00)
    sgpa = db.Column(db.Float, nullable=False)

    # Optional uploaded marksheet file reference
    file_path = db.Column(db.String(500), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    file_type = db.Column(db.String(20), nullable=True)

    # Mentor verification status: 'pending', 'verified', 'rejected'
    verification_status = db.Column(
        db.String(20),
        nullable=False,
        default='pending',
        server_default='pending'
    )

    # Reference to the mentor who verified/reviewed the marksheet
    verified_by_mentor_id = db.Column(
        db.Integer,
        db.ForeignKey('mentor_profiles.id', ondelete='SET NULL'),
        nullable=True
    )

    # Timestamp of when mentor reviewed the record
    verified_at = db.Column(db.DateTime, nullable=True)

    # Optional feedback or review note provided by the reviewing mentor
    review_note = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Unique constraint preventing duplicate records for the same mentee and semester
    __table_args__ = (
        db.UniqueConstraint('mentee_id', 'semester', name='uq_mentee_semester'),
    )

    # Relationships
    mentee = db.relationship('MenteeProfile', backref=db.backref('academic_records', lazy=True, cascade='all, delete-orphan'))
    verified_by = db.relationship('MentorProfile', backref=db.backref('verified_academic_records', lazy=True))

    def __init__(self, **kwargs):
        kwargs.setdefault('verification_status', 'pending')
        kwargs.setdefault('created_at', datetime.now(timezone.utc))
        kwargs.setdefault('updated_at', datetime.now(timezone.utc))
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<AcademicRecord id={self.id} mentee_id={self.mentee_id} semester={self.semester} sgpa={self.sgpa}>"
