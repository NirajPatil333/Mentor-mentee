"""
Skill model representing the 'skills' table in MySQL.
Shared skills catalog for mentors and mentees.
"""

from extensions import db


class Skill(db.Model):
    """
    Stores individual skills categorized for mentors and mentees to associate with.
    """
    __tablename__ = 'skills'

    # Primary key, auto-incrementing integer
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Unique skill name (e.g. 'Python', 'Machine Learning', 'Public Speaking')
    name = db.Column(db.String(100), unique=True, nullable=False)

    # Optional category grouping (e.g. 'Programming', 'Data Science', 'Soft Skills')
    category = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"<Skill id={self.id} name='{self.name}' category='{self.category}'>"
