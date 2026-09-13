"""
User model representing the 'users' table in MySQL.
"""

from datetime import datetime, timezone
from extensions import db


class User(db.Model):
    """
    User database model representing application users (mentors, mentees, admins).
    """
    __tablename__ = 'users'

    # Primary key, automatically increments with each new user
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Full name of the user
    name = db.Column(db.String(100), nullable=False)

    # Unique email address used for identification
    email = db.Column(db.String(120), unique=True, nullable=False)

    # Secure hashed password string
    password_hash = db.Column(db.String(255), nullable=False)

    # Role assigned to the user (e.g. 'mentor', 'mentee', 'admin')
    role = db.Column(db.String(20), nullable=False)

    # Timestamp recording when the user account was created
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<User {self.email} (Role: {self.role})>"
