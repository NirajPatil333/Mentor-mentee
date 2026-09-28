"""
Safe and idempotent skills catalog seeder.
Inserts foundational skills into the 'skills' table only if they do not already exist.
"""

from app import app
from extensions import db
from models import Skill

INITIAL_SKILLS = [
    # Programming
    {"name": "Python", "category": "Programming"},
    {"name": "JavaScript", "category": "Programming"},
    {"name": "TypeScript", "category": "Programming"},
    {"name": "Java", "category": "Programming"},
    {"name": "C++", "category": "Programming"},
    {"name": "Go", "category": "Programming"},

    # Web Development
    {"name": "React", "category": "Web Development"},
    {"name": "Node.js", "category": "Web Development"},
    {"name": "Flask", "category": "Web Development"},
    {"name": "HTML & CSS", "category": "Web Development"},

    # Data Science & AI
    {"name": "Machine Learning", "category": "Data Science & AI"},
    {"name": "Data Analysis", "category": "Data Science & AI"},
    {"name": "Deep Learning", "category": "Data Science & AI"},
    {"name": "SQL & Databases", "category": "Data Science & AI"},

    # Cloud & DevOps
    {"name": "Docker & Containers", "category": "Cloud & DevOps"},
    {"name": "AWS Cloud", "category": "Cloud & DevOps"},
    {"name": "CI/CD Pipelines", "category": "Cloud & DevOps"},
    {"name": "System Architecture", "category": "Cloud & DevOps"},

    # Soft Skills
    {"name": "Technical Communication", "category": "Soft Skills"},
    {"name": "Interview Preparation", "category": "Soft Skills"},
    {"name": "Career Growth", "category": "Soft Skills"},
]


def seed_skills():
    """
    Seeds initial skills idempotently without inserting duplicates.
    """
    with app.app_context():
        inserted_count = 0
        for skill_data in INITIAL_SKILLS:
            existing = Skill.query.filter_by(name=skill_data["name"]).first()
            if not existing:
                new_skill = Skill(name=skill_data["name"], category=skill_data["category"])
                db.session.add(new_skill)
                inserted_count += 1

        if inserted_count > 0:
            db.session.commit()
            print(f"[SUCCESS] Seeded {inserted_count} new skills into the catalog.")
        else:
            print("[INFO] All default skills already exist. No new skills were inserted.")

        total_skills = Skill.query.count()
        print(f"[INFO] Total skills in catalog: {total_skills}")
        return total_skills


if __name__ == '__main__':
    seed_skills()
