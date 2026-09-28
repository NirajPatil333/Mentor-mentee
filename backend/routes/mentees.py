"""
Mentee profile and learning interest management API endpoints.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from extensions import db
from models import MenteeProfile, LearningInterest, Skill
from utils.auth import mentee_required

mentees_bp = Blueprint('mentees', __name__)


@mentees_bp.route('/profile', methods=['GET'])
@mentee_required
def get_mentee_profile():
    """
    Retrieves the authenticated mentee's own profile.
    """
    user_id = int(get_jwt_identity())
    profile = MenteeProfile.query.filter_by(user_id=user_id).first()

    if not profile:
        # If profile doesn't exist yet, auto-create an initial empty profile
        profile = MenteeProfile(user_id=user_id)
        db.session.add(profile)
        db.session.commit()

    return jsonify({
        "status": "success",
        "profile": {
            "id": profile.id,
            "user_id": profile.user_id,
            "bio": profile.bio or "",
            "education": profile.education or "",
            "learning_goal": profile.learning_goal or "",
            "experience_level": profile.experience_level or ""
        }
    }), 200


@mentees_bp.route('/profile', methods=['PUT'])
@mentee_required
def update_mentee_profile():
    """
    Creates or updates the authenticated mentee's own profile.
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    profile = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = MenteeProfile(user_id=user_id)
        db.session.add(profile)

    # Update allowed fields if provided in request
    if 'bio' in data:
        profile.bio = data.get('bio', '')
    if 'education' in data:
        profile.education = data.get('education', '')
    if 'learning_goal' in data:
        profile.learning_goal = data.get('learning_goal', '')
    if 'experience_level' in data:
        profile.experience_level = data.get('experience_level', '')

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Mentee profile updated successfully",
        "profile": {
            "id": profile.id,
            "user_id": profile.user_id,
            "bio": profile.bio or "",
            "education": profile.education or "",
            "learning_goal": profile.learning_goal or "",
            "experience_level": profile.experience_level or ""
        }
    }), 200


@mentees_bp.route('/interests', methods=['GET'])
@mentee_required
def get_mentee_interests():
    """
    Retrieves all learning interests associated with the authenticated mentee.
    """
    user_id = int(get_jwt_identity())
    profile = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return jsonify({
            "status": "success",
            "interests": []
        }), 200

    interests = (
        db.session.query(LearningInterest, Skill)
        .join(Skill, LearningInterest.skill_id == Skill.id)
        .filter(LearningInterest.mentee_id == profile.id)
        .all()
    )

    interests_data = [
        {
            "id": interest.id,
            "skill_id": skill.id,
            "skill_name": skill.name,
            "category": skill.category,
            "priority": interest.priority
        }
        for interest, skill in interests
    ]

    return jsonify({
        "status": "success",
        "interests": interests_data
    }), 200


@mentees_bp.route('/interests', methods=['PUT'])
@mentee_required
def update_mentee_interests():
    """
    Replaces the authenticated mentee's learning interests.
    Validates skill existence and ensures no duplicate skill associations.
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)
    if not data or 'interests' not in data or not isinstance(data['interests'], list):
        return jsonify({
            "status": "error",
            "message": "Request body must contain an 'interests' list"
        }), 400

    interests_list = data['interests']

    # Ensure profile exists
    profile = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = MenteeProfile(user_id=user_id)
        db.session.add(profile)
        db.session.flush()

    # Validate duplicate skill_ids in request
    skill_ids_in_req = []
    for item in interests_list:
        if not isinstance(item, dict) or 'skill_id' not in item:
            return jsonify({
                "status": "error",
                "message": "Each interest item must include 'skill_id'"
            }), 400

        sid = item['skill_id']
        if sid in skill_ids_in_req:
            return jsonify({
                "status": "error",
                "message": f"Duplicate skill_id {sid} detected in interests list"
            }), 400
        skill_ids_in_req.append(sid)

    # Validate that all referenced skills exist in catalog
    if skill_ids_in_req:
        existing_skills = Skill.query.filter(Skill.id.in_(skill_ids_in_req)).all()
        existing_skill_ids = {s.id for s in existing_skills}
        missing_ids = set(skill_ids_in_req) - existing_skill_ids
        if missing_ids:
            return jsonify({
                "status": "error",
                "message": f"Referenced skill IDs not found in catalog: {list(missing_ids)}"
            }), 400

    # Atomically replace interests
    try:
        # Delete old interests
        LearningInterest.query.filter_by(mentee_id=profile.id).delete()

        # Add new interests
        for item in interests_list:
            priority = str(item.get('priority', '1'))
            new_interest = LearningInterest(
                mentee_id=profile.id,
                skill_id=item['skill_id'],
                priority=priority
            )
            db.session.add(new_interest)

        db.session.commit()

        # Fetch saved interests for clean response
        saved = (
            db.session.query(LearningInterest, Skill)
            .join(Skill, LearningInterest.skill_id == Skill.id)
            .filter(LearningInterest.mentee_id == profile.id)
            .all()
        )
        saved_data = [
            {
                "id": interest.id,
                "skill_id": skill.id,
                "skill_name": skill.name,
                "category": skill.category,
                "priority": interest.priority
            }
            for interest, skill in saved
        ]

        return jsonify({
            "status": "success",
            "message": "Mentee learning interests updated successfully",
            "interests": saved_data
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to update learning interests: {str(e)}"
        }), 500
