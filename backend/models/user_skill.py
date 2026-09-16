"""
UserSkill model representing the 'user_skills' association table in MySQL.
Associates users (mentors and mentees) with skills from the shared catalog,
including optional proficiency levels.
"""

from extensions import db


class UserSkill(db.Model):
    """
    Stores skill associations for users with their proficiency level.
    Enforces a composite unique constraint on (user_id, skill_id)
    to prevent duplicate skill entries per user.
    """
    __tablename__ = 'user_skills'

    # Primary key, auto-incrementing integer
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign key referencing the users table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Foreign key referencing the skills table
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)

    # Optional proficiency level (e.g. 'Beginner', 'Intermediate', 'Expert')
    proficiency = db.Column(db.String(50), nullable=True)

    # Composite UNIQUE constraint to prevent duplicate skills per user
    __table_args__ = (
        db.UniqueConstraint('user_id', 'skill_id', name='uq_user_skill'),
    )

    # Relationships to access associated User and Skill models
    user = db.relationship('User', backref=db.backref('user_skills', lazy=True))
    skill = db.relationship('Skill', backref=db.backref('user_skills', lazy=True))

    def __repr__(self):
        return f"<UserSkill id={self.id} user_id={self.user_id} skill_id={self.skill_id} proficiency='{self.proficiency}'>"
