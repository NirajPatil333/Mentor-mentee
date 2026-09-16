"""
MenteeProfile model representing the 'mentee_profiles' table in MySQL.
"""

from extensions import db


class MenteeProfile(db.Model):
    """
    Stores detailed profile information for users who are mentees.
    Has a one-to-one relationship with the User model.
    """
    __tablename__ = 'mentee_profiles'

    # Primary key, auto-incrementing integer
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign key referencing the users table (unique=True enforces 1-to-1 relationship)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)

    # Optional mentee profile details
    bio = db.Column(db.Text, nullable=True)
    education = db.Column(db.String(255), nullable=True)
    learning_goal = db.Column(db.Text, nullable=True)
    experience_level = db.Column(db.String(50), nullable=True)

    # Relationship to access the associated User instance directly
    user = db.relationship('User', backref=db.backref('mentee_profile', uselist=False))

    def __repr__(self):
        return f"<MenteeProfile id={self.id} user_id={self.user_id}>"
