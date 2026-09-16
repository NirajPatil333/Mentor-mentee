"""
LearningInterest model representing the 'learning_interests' association table in MySQL.
Associates mentee profiles with skills they are interested in learning,
including an optional priority level.
"""

from extensions import db


class LearningInterest(db.Model):
    """
    Stores learning interests for mentees linked to skills with priority.
    Enforces a composite unique constraint on (mentee_id, skill_id)
    to prevent duplicate interest entries per mentee profile.
    """
    __tablename__ = 'learning_interests'

    # Primary key, auto-incrementing integer
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign key referencing the mentee_profiles table
    mentee_id = db.Column(db.Integer, db.ForeignKey('mentee_profiles.id'), nullable=False)

    # Foreign key referencing the skills table
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)

    # Optional priority level (e.g. 'High', 'Medium', 'Low')
    priority = db.Column(db.String(20), nullable=True)

    # Composite UNIQUE constraint to prevent duplicate interests per mentee profile
    __table_args__ = (
        db.UniqueConstraint('mentee_id', 'skill_id', name='uq_learning_interest'),
    )

    # Relationships to access associated MenteeProfile and Skill models
    mentee = db.relationship('MenteeProfile', backref=db.backref('learning_interests', lazy=True))
    skill = db.relationship('Skill', backref=db.backref('learning_interests', lazy=True))

    def __repr__(self):
        return f"<LearningInterest id={self.id} mentee_id={self.mentee_id} skill_id={self.skill_id} priority='{self.priority}'>"
