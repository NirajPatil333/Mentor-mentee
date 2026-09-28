"""
Skills catalog API endpoints.
Provides access to standardized skills list for mentors and mentees.
"""

from flask import Blueprint, jsonify
from models import Skill

skills_bp = Blueprint('skills', __name__)


@skills_bp.route('', methods=['GET'])
@skills_bp.route('/', methods=['GET'])
def get_skills():
    """
    Retrieves all available skills in the catalog.
    Publicly accessible or usable by authenticated users.
    """
    skills = Skill.query.order_by(Skill.category, Skill.name).all()
    skills_data = [
        {
            "id": skill.id,
            "name": skill.name,
            "category": skill.category
        }
        for skill in skills
    ]
    return jsonify({
        "status": "success",
        "count": len(skills_data),
        "skills": skills_data
    }), 200
