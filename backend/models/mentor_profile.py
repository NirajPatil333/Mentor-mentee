"""
MentorProfile model representing the 'mentor_profiles' table in MySQL.
"""

from extensions import db


class MentorProfile(db.Model):
    """
    Stores detailed profile information for users who are mentors.
    Has a one-to-one relationship with the User model.
    """
    __tablename__ = 'mentor_profiles'

    # Primary key, auto-incrementing integer
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign key referencing the users table (unique=True enforces 1-to-1 relationship)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)

    # Optional mentor profile details
    bio = db.Column(db.Text, nullable=True)
    experience_years = db.Column(db.Integer, nullable=True)
    education = db.Column(db.String(255), nullable=True)
    current_position = db.Column(db.String(150), nullable=True)
    availability_status = db.Column(db.String(50), nullable=True)

    # Performance metrics with default values
    average_rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)

    # Relationship to access the associated User instance directly
    user = db.relationship('User', backref=db.backref('mentor_profile', uselist=False))

    def __repr__(self):
        return f"<MentorProfile id={self.id} user_id={self.user_id}>"
