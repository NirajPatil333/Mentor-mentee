"""
MentorAvailability model representing the 'mentor_availability' table in MySQL.
Stores weekly recurring time slots when mentors are available for mentoring sessions.
"""

from extensions import db


class MentorAvailability(db.Model):
    """
    Stores recurring availability slots for mentors.
    Linked to MentorProfile via mentor_id.
    """
    __tablename__ = 'mentor_availability'

    # Primary key, auto-incrementing integer
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign key referencing the mentor_profiles table
    mentor_id = db.Column(db.Integer, db.ForeignKey('mentor_profiles.id'), nullable=False)

    # Day of the week (e.g. 'Monday', 'Tuesday', etc.)
    day_of_week = db.Column(db.String(15), nullable=False)

    # Available time window
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    # Relationship to access the associated MentorProfile model
    mentor = db.relationship('MentorProfile', backref=db.backref('availabilities', lazy=True))

    def __repr__(self):
        return (
            f"<MentorAvailability id={self.id} mentor_id={self.mentor_id} "
            f"day='{self.day_of_week}' {self.start_time}-{self.end_time}>"
        )
