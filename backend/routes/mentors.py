"""
Mentor profile, skills, availability, and mentee recommendations API endpoints.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from extensions import db
from models import MentorProfile, UserSkill, Skill, MentorAvailability
from utils.auth import mentor_required, mentee_required
from services.matching_service import calculate_mentor_recommendations

mentors_bp = Blueprint('mentors', __name__)

VALID_DAYS_OF_WEEK = {
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
}


def parse_time_str(time_str: str):
    """
    Parses a time string in 'HH:MM' or 'HH:MM:SS' format into a datetime.time object.
    Returns None if the format is invalid.
    """
    if not isinstance(time_str, str):
        return None
    for fmt in ('%H:%M:%S', '%H:%M'):
        try:
            return datetime.strptime(time_str.strip(), fmt).time()
        except ValueError:
            continue
    return None


@mentors_bp.route('/profile', methods=['GET'])
@mentor_required
def get_mentor_profile():
    """
    Retrieves the authenticated mentor's own profile.
    """
    user_id = int(get_jwt_identity())
    profile = MentorProfile.query.filter_by(user_id=user_id).first()

    if not profile:
        profile = MentorProfile(user_id=user_id)
        db.session.add(profile)
        db.session.commit()

    return jsonify({
        "status": "success",
        "profile": {
            "id": profile.id,
            "user_id": profile.user_id,
            "bio": profile.bio or "",
            "experience_years": profile.experience_years or 0,
            "education": profile.education or "",
            "current_position": profile.current_position or "",
            "availability_status": profile.availability_status or "available",
            "average_rating": profile.average_rating or 0.0,
            "total_reviews": profile.total_reviews or 0
        }
    }), 200


@mentors_bp.route('/profile', methods=['PUT'])
@mentor_required
def update_mentor_profile():
    """
    Creates or updates the authenticated mentor's own profile.
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    profile = MentorProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = MentorProfile(user_id=user_id)
        db.session.add(profile)

    if 'bio' in data:
        profile.bio = data.get('bio', '')
    if 'experience_years' in data:
        try:
            profile.experience_years = int(data.get('experience_years', 0))
        except (ValueError, TypeError):
            profile.experience_years = 0
    if 'education' in data:
        profile.education = data.get('education', '')
    if 'current_position' in data:
        profile.current_position = data.get('current_position', '')
    if 'availability_status' in data:
        profile.availability_status = data.get('availability_status', 'available')

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Mentor profile updated successfully",
        "profile": {
            "id": profile.id,
            "user_id": profile.user_id,
            "bio": profile.bio or "",
            "experience_years": profile.experience_years or 0,
            "education": profile.education or "",
            "current_position": profile.current_position or "",
            "availability_status": profile.availability_status or "available",
            "average_rating": profile.average_rating or 0.0,
            "total_reviews": profile.total_reviews or 0
        }
    }), 200


@mentors_bp.route('/skills', methods=['GET'])
@mentor_required
def get_mentor_skills():
    """
    Retrieves all skills and proficiencies declared by the authenticated mentor.
    """
    user_id = int(get_jwt_identity())

    skills = (
        db.session.query(UserSkill, Skill)
        .join(Skill, UserSkill.skill_id == Skill.id)
        .filter(UserSkill.user_id == user_id)
        .all()
    )

    skills_data = [
        {
            "id": us.id,
            "skill_id": skill.id,
            "skill_name": skill.name,
            "category": skill.category,
            "proficiency": us.proficiency or ""
        }
        for us, skill in skills
    ]

    return jsonify({
        "status": "success",
        "skills": skills_data
    }), 200


@mentors_bp.route('/skills', methods=['PUT'])
@mentor_required
def update_mentor_skills():
    """
    Replaces the authenticated mentor's skills catalog associations.
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)
    if not data or 'skills' not in data or not isinstance(data['skills'], list):
        return jsonify({
            "status": "error",
            "message": "Request body must contain a 'skills' list"
        }), 400

    skills_list = data['skills']

    # Validate duplicate skill_ids in payload
    skill_ids_in_req = []
    for item in skills_list:
        if not isinstance(item, dict) or 'skill_id' not in item:
            return jsonify({
                "status": "error",
                "message": "Each item in 'skills' must include 'skill_id'"
            }), 400

        sid = item['skill_id']
        if sid in skill_ids_in_req:
            return jsonify({
                "status": "error",
                "message": f"Duplicate skill_id {sid} detected in skills list"
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

    try:
        # Atomically delete previous associations for this user
        UserSkill.query.filter_by(user_id=user_id).delete()

        # Insert new skill associations
        for item in skills_list:
            proficiency = str(item.get('proficiency', '')).strip()
            new_user_skill = UserSkill(
                user_id=user_id,
                skill_id=item['skill_id'],
                proficiency=proficiency
            )
            db.session.add(new_user_skill)

        db.session.commit()

        # Query updated entries
        saved = (
            db.session.query(UserSkill, Skill)
            .join(Skill, UserSkill.skill_id == Skill.id)
            .filter(UserSkill.user_id == user_id)
            .all()
        )
        saved_data = [
            {
                "id": us.id,
                "skill_id": skill.id,
                "skill_name": skill.name,
                "category": skill.category,
                "proficiency": us.proficiency or ""
            }
            for us, skill in saved
        ]

        return jsonify({
            "status": "success",
            "message": "Mentor skills updated successfully",
            "skills": saved_data
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to update mentor skills: {str(e)}"
        }), 500


@mentors_bp.route('/availability', methods=['GET'])
@mentor_required
def get_mentor_availability():
    """
    Retrieves the authenticated mentor's recurring availability slots.
    """
    user_id = int(get_jwt_identity())
    profile = MentorProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return jsonify({
            "status": "success",
            "availability": []
        }), 200

    slots = MentorAvailability.query.filter_by(mentor_id=profile.id).order_by(
        MentorAvailability.day_of_week, MentorAvailability.start_time
    ).all()

    slots_data = [
        {
            "id": slot.id,
            "day_of_week": slot.day_of_week,
            "start_time": slot.start_time.strftime('%H:%M:%S'),
            "end_time": slot.end_time.strftime('%H:%M:%S')
        }
        for slot in slots
    ]

    return jsonify({
        "status": "success",
        "availability": slots_data
    }), 200


@mentors_bp.route('/availability', methods=['PUT'])
@mentor_required
def update_mentor_availability():
    """
    Replaces the authenticated mentor's recurring availability schedule.
    Validates day and ensures start_time is strictly before end_time.
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)
    if not data or 'availability' not in data or not isinstance(data['availability'], list):
        return jsonify({
            "status": "error",
            "message": "Request body must contain an 'availability' list"
        }), 400

    profile = MentorProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = MentorProfile(user_id=user_id)
        db.session.add(profile)
        db.session.flush()

    validated_slots = []
    for item in data['availability']:
        if not isinstance(item, dict):
            return jsonify({
                "status": "error",
                "message": "Each availability slot must be a JSON object"
            }), 400

        day = str(item.get('day_of_week', '')).strip()
        if day.lower() not in VALID_DAYS_OF_WEEK:
            return jsonify({
                "status": "error",
                "message": f"Invalid day_of_week: '{day}'. Must be one of Monday through Sunday."
            }), 400

        start_str = item.get('start_time')
        end_str = item.get('end_time')

        start_time_obj = parse_time_str(start_str)
        end_time_obj = parse_time_str(end_str)

        if not start_time_obj or not end_time_obj:
            return jsonify({
                "status": "error",
                "message": "Invalid time format for start_time or end_time. Expected 'HH:MM' or 'HH:MM:SS'."
            }), 400

        if start_time_obj >= end_time_obj:
            return jsonify({
                "status": "error",
                "message": f"start_time ({start_str}) must be strictly earlier than end_time ({end_str})"
            }), 400

        validated_slots.append({
            "day_of_week": day.capitalize(),
            "start_time": start_time_obj,
            "end_time": end_time_obj
        })

    try:
        # Delete prior slots for this mentor
        MentorAvailability.query.filter_by(mentor_id=profile.id).delete()

        # Insert new slots
        for slot in validated_slots:
            new_slot = MentorAvailability(
                mentor_id=profile.id,
                day_of_week=slot['day_of_week'],
                start_time=slot['start_time'],
                end_time=slot['end_time']
            )
            db.session.add(new_slot)

        db.session.commit()

        # Fetch saved slots for response
        saved = MentorAvailability.query.filter_by(mentor_id=profile.id).order_by(
            MentorAvailability.day_of_week, MentorAvailability.start_time
        ).all()
        saved_data = [
            {
                "id": s.id,
                "day_of_week": s.day_of_week,
                "start_time": s.start_time.strftime('%H:%M:%S'),
                "end_time": s.end_time.strftime('%H:%M:%S')
            }
            for s in saved
        ]

        return jsonify({
            "status": "success",
            "message": "Mentor availability updated successfully",
            "availability": saved_data
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to update availability: {str(e)}"
        }), 500


@mentors_bp.route('/recommendations', methods=['GET'])
@mentee_required
def get_recommendations():
    """
    Computes rule-based mentor recommendations for the authenticated mentee.
    Ranks mentors by compatibility score and provides clear score component breakdowns.
    """
    user_id = int(get_jwt_identity())
    recommendations = calculate_mentor_recommendations(user_id)

    return jsonify({
        "status": "success",
        "count": len(recommendations),
        "recommendations": recommendations
    }), 200
