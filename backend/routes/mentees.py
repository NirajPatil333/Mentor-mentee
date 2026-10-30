"""
Mentee profile, skills, learning interests, and mentor evaluation API endpoints.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from extensions import db
from models import (
    MenteeProfile, LearningInterest, Skill, Certificate, Achievement,
    MentorProfile, MentorshipRequest, AcademicRecord, UserSkill, User
)
from utils.auth import mentee_required, mentor_required, get_current_user
from routes.certificates import format_certificate
from routes.achievements import format_achievement
from routes.academic_records import format_academic_record, calculate_cgpa
from routes.auth import handle_profile_picture_upload, handle_profile_picture_delete

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
        profile = MenteeProfile(user_id=user_id)
        db.session.add(profile)
        db.session.commit()

    user = profile.user
    return jsonify({
        "status": "success",
        "profile": {
            "id": profile.id,
            "user_id": profile.user_id,
            "name": user.name if user else "",
            "email": user.email if user else "",
            "profile_picture": user.profile_picture if user else None,
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

    user = profile.user
    return jsonify({
        "status": "success",
        "message": "Mentee profile updated successfully",
        "profile": {
            "id": profile.id,
            "user_id": profile.user_id,
            "name": user.name if user else "",
            "email": user.email if user else "",
            "profile_picture": user.profile_picture if user else None,
            "bio": profile.bio or "",
            "education": profile.education or "",
            "learning_goal": profile.learning_goal or "",
            "experience_level": profile.experience_level or ""
        }
    }), 200


@mentees_bp.route('/profile-picture', methods=['POST'])
@mentee_required
def upload_mentee_profile_picture():
    """
    Uploads or updates the authenticated mentee's profile picture.
    """
    user = get_current_user()
    if not user:
        return jsonify({"status": "error", "message": "Mentee account not found"}), 404
    return handle_profile_picture_upload(user)


@mentees_bp.route('/profile-picture', methods=['DELETE'])
@mentee_required
def delete_mentee_profile_picture():
    """
    Removes the authenticated mentee's profile picture.
    """
    user = get_current_user()
    if not user:
        return jsonify({"status": "error", "message": "Mentee account not found"}), 404
    return handle_profile_picture_delete(user)


# ---------------------------------------------------------------------------
# Section A: My Skills (Technologies the mentee already knows)
# Stored in `user_skills` table (user_id = mentee.user_id)
# ---------------------------------------------------------------------------

@mentees_bp.route('/skills', methods=['GET'])
@mentee_required
def get_mentee_skills():
    """
    Retrieves all skills declared as known by the authenticated mentee.
    """
    user_id = int(get_jwt_identity())

    skills = (
        db.session.query(UserSkill, Skill)
        .join(Skill, UserSkill.skill_id == Skill.id)
        .filter(UserSkill.user_id == user_id)
        .order_by(Skill.name.asc())
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


@mentees_bp.route('/skills', methods=['POST'])
@mentee_required
def add_mentee_skill():
    """
    Adds or updates a single known skill for the authenticated mentee.
    Supports either skill_id or skill_name.
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    skill_id = data.get('skill_id')
    skill_name = data.get('skill_name')
    proficiency = str(data.get('proficiency', 'Intermediate')).strip()

    if not skill_id and not skill_name:
        return jsonify({
            "status": "error",
            "message": "Either 'skill_id' or 'skill_name' is required"
        }), 400

    if not skill_id and skill_name:
        clean_name = str(skill_name).strip()
        skill = Skill.query.filter(Skill.name.ilike(clean_name)).first()
        if not skill:
            skill = Skill(name=clean_name, category=data.get('category', 'Technical'))
            db.session.add(skill)
            db.session.flush()
        skill_id = skill.id
    else:
        try:
            skill_id = int(skill_id)
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Invalid skill_id"}), 400
        skill = Skill.query.get(skill_id)
        if not skill:
            return jsonify({"status": "error", "message": f"Skill {skill_id} not found"}), 404

    existing = UserSkill.query.filter_by(user_id=user_id, skill_id=skill_id).first()
    if existing:
        existing.proficiency = proficiency
    else:
        new_us = UserSkill(user_id=user_id, skill_id=skill_id, proficiency=proficiency)
        db.session.add(new_us)

    db.session.commit()
    return get_mentee_skills()


@mentees_bp.route('/skills/<int:skill_id>', methods=['DELETE'])
@mentee_required
def delete_mentee_skill(skill_id: int):
    """
    Deletes a single known skill for the authenticated mentee.
    """
    user_id = int(get_jwt_identity())
    UserSkill.query.filter_by(user_id=user_id, skill_id=skill_id).delete()
    db.session.commit()
    return get_mentee_skills()


@mentees_bp.route('/skills', methods=['PUT'])
@mentee_required
def update_mentee_skills():
    """
    Replaces the authenticated mentee's known skills catalog associations.
    Accepts items with skill_id or skill_name.
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)
    if not data or 'skills' not in data or not isinstance(data['skills'], list):
        return jsonify({
            "status": "error",
            "message": "Request body must contain a 'skills' list"
        }), 400

    skills_list = data['skills']
    processed_items = []
    seen_skill_ids = set()

    for item in skills_list:
        if not isinstance(item, dict):
            return jsonify({"status": "error", "message": "Each item in 'skills' must be an object"}), 400

        sid = item.get('skill_id')
        sname = item.get('skill_name')

        if not sid and not sname:
            return jsonify({"status": "error", "message": "Each skill item must have 'skill_id' or 'skill_name'"}), 400

        if not sid and sname:
            clean_name = str(sname).strip()
            skill_obj = Skill.query.filter(Skill.name.ilike(clean_name)).first()
            if not skill_obj:
                skill_obj = Skill(name=clean_name, category=item.get('category', 'Technical'))
                db.session.add(skill_obj)
                db.session.flush()
            sid = skill_obj.id
        else:
            try:
                sid = int(sid)
            except (ValueError, TypeError):
                return jsonify({"status": "error", "message": f"Invalid skill_id: {sid}"}), 400
            skill_obj = Skill.query.get(sid)
            if not skill_obj:
                return jsonify({"status": "error", "message": f"Referenced skill ID {sid} not found in catalog"}), 400

        if sid in seen_skill_ids:
            return jsonify({"status": "error", "message": f"Duplicate skill ID {sid} detected in skills list"}), 400

        seen_skill_ids.add(sid)
        processed_items.append({
            "skill_id": sid,
            "proficiency": str(item.get('proficiency', '')).strip()
        })

    try:
        # Atomically delete previous associations for this user
        UserSkill.query.filter_by(user_id=user_id).delete()

        for item in processed_items:
            new_user_skill = UserSkill(
                user_id=user_id,
                skill_id=item['skill_id'],
                proficiency=item['proficiency']
            )
            db.session.add(new_user_skill)

        db.session.commit()

        saved = (
            db.session.query(UserSkill, Skill)
            .join(Skill, UserSkill.skill_id == Skill.id)
            .filter(UserSkill.user_id == user_id)
            .order_by(Skill.name.asc())
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
            "message": "Mentee skills updated successfully",
            "skills": saved_data
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to update mentee skills: {str(e)}"
        }), 500


# ---------------------------------------------------------------------------
# Section B: Skills I Want to Learn (Learning Interests)
# Stored in `learning_interests` table (mentee_id = mentee_profile.id)
# ---------------------------------------------------------------------------

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
        .order_by(Skill.name.asc())
        .all()
    )

    interests_data = [
        {
            "id": interest.id,
            "skill_id": skill.id,
            "skill_name": skill.name,
            "category": skill.category,
            "priority": interest.priority or "High"
        }
        for interest, skill in interests
    ]

    return jsonify({
        "status": "success",
        "interests": interests_data
    }), 200


@mentees_bp.route('/interests', methods=['POST'])
@mentee_required
def add_mentee_interest():
    """
    Adds or updates a single learning interest for the authenticated mentee.
    """
    user_id = int(get_jwt_identity())
    profile = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = MenteeProfile(user_id=user_id)
        db.session.add(profile)
        db.session.flush()

    data = request.get_json(silent=True) or {}
    skill_id = data.get('skill_id')
    skill_name = data.get('skill_name')
    priority = str(data.get('priority', 'High')).strip()

    if not skill_id and not skill_name:
        return jsonify({
            "status": "error",
            "message": "Either 'skill_id' or 'skill_name' is required"
        }), 400

    if not skill_id and skill_name:
        clean_name = str(skill_name).strip()
        skill = Skill.query.filter(Skill.name.ilike(clean_name)).first()
        if not skill:
            skill = Skill(name=clean_name, category=data.get('category', 'Technical'))
            db.session.add(skill)
            db.session.flush()
        skill_id = skill.id
    else:
        try:
            skill_id = int(skill_id)
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Invalid skill_id"}), 400
        skill = Skill.query.get(skill_id)
        if not skill:
            return jsonify({"status": "error", "message": f"Skill {skill_id} not found"}), 404

    existing = LearningInterest.query.filter_by(mentee_id=profile.id, skill_id=skill_id).first()
    if existing:
        existing.priority = priority
    else:
        new_li = LearningInterest(mentee_id=profile.id, skill_id=skill_id, priority=priority)
        db.session.add(new_li)

    db.session.commit()
    return get_mentee_interests()


@mentees_bp.route('/interests/<int:skill_id>', methods=['DELETE'])
@mentee_required
def delete_mentee_interest(skill_id: int):
    """
    Deletes a single learning interest for the authenticated mentee.
    """
    user_id = int(get_jwt_identity())
    profile = MenteeProfile.query.filter_by(user_id=user_id).first()
    if profile:
        LearningInterest.query.filter_by(mentee_id=profile.id, skill_id=skill_id).delete()
        db.session.commit()
    return get_mentee_interests()


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

    profile = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = MenteeProfile(user_id=user_id)
        db.session.add(profile)
        db.session.flush()

    processed_items = []
    seen_skill_ids = set()

    for item in interests_list:
        if not isinstance(item, dict):
            return jsonify({"status": "error", "message": "Each interest item must be an object"}), 400

        sid = item.get('skill_id')
        sname = item.get('skill_name')

        if not sid and not sname:
            return jsonify({"status": "error", "message": "Each interest item must have 'skill_id' or 'skill_name'"}), 400

        if not sid and sname:
            clean_name = str(sname).strip()
            skill_obj = Skill.query.filter(Skill.name.ilike(clean_name)).first()
            if not skill_obj:
                skill_obj = Skill(name=clean_name, category=item.get('category', 'Technical'))
                db.session.add(skill_obj)
                db.session.flush()
            sid = skill_obj.id
        else:
            try:
                sid = int(sid)
            except (ValueError, TypeError):
                return jsonify({"status": "error", "message": f"Invalid skill_id: {sid}"}), 400
            skill_obj = Skill.query.get(sid)
            if not skill_obj:
                return jsonify({"status": "error", "message": f"Referenced skill ID {sid} not found in catalog"}), 400

        if sid in seen_skill_ids:
            return jsonify({"status": "error", "message": f"Duplicate skill ID {sid} detected in interests list"}), 400

        seen_skill_ids.add(sid)
        processed_items.append({
            "skill_id": sid,
            "priority": str(item.get('priority', 'High')).strip() or 'High'
        })

    try:
        LearningInterest.query.filter_by(mentee_id=profile.id).delete()

        for item in processed_items:
            new_interest = LearningInterest(
                mentee_id=profile.id,
                skill_id=item['skill_id'],
                priority=item['priority']
            )
            db.session.add(new_interest)

        db.session.commit()

        saved = (
            db.session.query(LearningInterest, Skill)
            .join(Skill, LearningInterest.skill_id == Skill.id)
            .filter(LearningInterest.mentee_id == profile.id)
            .order_by(Skill.name.asc())
            .all()
        )
        saved_data = [
            {
                "id": interest.id,
                "skill_id": skill.id,
                "skill_name": skill.name,
                "category": skill.category,
                "priority": interest.priority or "High"
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


# ---------------------------------------------------------------------------
# Mentee Full Profile Endpoint for Authorized Mentors
# ---------------------------------------------------------------------------

@mentees_bp.route('/<int:mentee_id>/profile', methods=['GET'])
@mentees_bp.route('/<int:mentee_id>', methods=['GET'])
@mentor_required
def get_mentee_full_profile(mentee_id: int):
    """
    Retrieves full background and profile information for a mentee.
    Restricted to authenticated mentors who have an incoming or active mentorship request with the mentee.
    """
    user_id = int(get_jwt_identity())
    mentor_prof = MentorProfile.query.filter_by(user_id=user_id).first()
    if not mentor_prof:
        return jsonify({"status": "error", "message": "Mentor profile not found"}), 403

    # Find mentee profile by ID or user_id
    mentee_prof = MenteeProfile.query.get(mentee_id)
    if not mentee_prof:
        mentee_prof = MenteeProfile.query.filter_by(user_id=mentee_id).first()

    if not mentee_prof:
        return jsonify({"status": "error", "message": f"Mentee profile with ID {mentee_id} not found"}), 404

    # Verify authorization: Mentor must have received a request from this mentee
    req = MentorshipRequest.query.filter_by(
        mentor_id=mentor_prof.id,
        mentee_id=mentee_prof.id
    ).first()

    if not req:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you do not have permission to view this mentee's profile"
        }), 403

    mentee_user = mentee_prof.user

    # Fetch mentee known skills
    known_skills_rows = (
        db.session.query(UserSkill, Skill)
        .join(Skill, UserSkill.skill_id == Skill.id)
        .filter(UserSkill.user_id == mentee_prof.user_id)
        .order_by(Skill.name.asc())
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
        for us, skill in known_skills_rows
    ]

    # Fetch mentee learning interests
    interests_rows = (
        db.session.query(LearningInterest, Skill)
        .join(Skill, LearningInterest.skill_id == Skill.id)
        .filter(LearningInterest.mentee_id == mentee_prof.id)
        .order_by(Skill.name.asc())
        .all()
    )
    interests_data = [
        {
            "id": interest.id,
            "skill_id": skill.id,
            "skill_name": skill.name,
            "category": skill.category,
            "priority": interest.priority or "High"
        }
        for interest, skill in interests_rows
    ]

    return jsonify({
        "status": "success",
        "mentee": {
            "id": mentee_prof.id,
            "user_id": mentee_prof.user_id,
            "name": mentee_user.name if mentee_user else "",
            "email": mentee_user.email if mentee_user else "",
            "profile_picture": mentee_user.profile_picture if mentee_user else None,
            "bio": mentee_prof.bio or "",
            "education": mentee_prof.education or "",
            "learning_goal": mentee_prof.learning_goal or "",
            "experience_level": mentee_prof.experience_level or "",
            "skills": skills_data,
            "learning_interests": interests_data,
            "request_status": req.status,
            "request_message": req.message or ""
        }
    }), 200


@mentees_bp.route('/<int:mentee_id>/certificates', methods=['GET'])
@mentor_required
def get_mentee_certificates(mentee_id: int):
    """
    Retrieves all certificates uploaded by a specific mentee.
    Restricted to authenticated mentors who have an accepted mentorship request.
    """
    user_id = int(get_jwt_identity())
    mentor_prof = MentorProfile.query.filter_by(user_id=user_id).first()
    if not mentor_prof:
        return jsonify({"status": "error", "message": "Mentor profile not found"}), 403

    mentee_prof = MenteeProfile.query.get(mentee_id)
    if not mentee_prof:
        mentee_prof = MenteeProfile.query.filter_by(user_id=mentee_id).first()

    if not mentee_prof:
        return jsonify({"status": "error", "message": f"Mentee profile with ID {mentee_id} not found"}), 404

    active_request = MentorshipRequest.query.filter_by(
        mentor_id=mentor_prof.id,
        mentee_id=mentee_prof.id,
        status='accepted'
    ).first()

    if not active_request:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you do not have an accepted mentorship with this mentee"
        }), 403

    certs = Certificate.query.filter_by(
        mentee_id=mentee_prof.id
    ).order_by(Certificate.issue_date.desc(), Certificate.created_at.desc()).all()

    certs_data = [format_certificate(c) for c in certs]
    return jsonify({
        "status": "success",
        "count": len(certs_data),
        "certificates": certs_data
    }), 200


@mentees_bp.route('/<int:mentee_id>/achievements', methods=['GET'])
@mentor_required
def get_mentee_achievements(mentee_id: int):
    """
    Retrieves all achievements recorded by a specific mentee.
    Restricted to authenticated mentors who have an accepted mentorship request.
    """
    user_id = int(get_jwt_identity())
    mentor_prof = MentorProfile.query.filter_by(user_id=user_id).first()
    if not mentor_prof:
        return jsonify({"status": "error", "message": "Mentor profile not found"}), 403

    mentee_prof = MenteeProfile.query.get(mentee_id)
    if not mentee_prof:
        mentee_prof = MenteeProfile.query.filter_by(user_id=mentee_id).first()

    if not mentee_prof:
        return jsonify({"status": "error", "message": f"Mentee profile with ID {mentee_id} not found"}), 404

    active_request = MentorshipRequest.query.filter_by(
        mentor_id=mentor_prof.id,
        mentee_id=mentee_prof.id,
        status='accepted'
    ).first()

    if not active_request:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you do not have an accepted mentorship with this mentee"
        }), 403

    achievements = Achievement.query.filter_by(
        mentee_id=mentee_prof.id
    ).order_by(Achievement.achievement_date.desc(), Achievement.created_at.desc()).all()

    achievements_data = [format_achievement(a) for a in achievements]
    return jsonify({
        "status": "success",
        "count": len(achievements_data),
        "achievements": achievements_data
    }), 200


@mentees_bp.route('/<int:mentee_id>/academic-records', methods=['GET'])
@mentor_required
def get_mentee_academic_records(mentee_id: int):
    """
    Retrieves all academic records and calculated CGPA for an accepted mentee.
    Restricted to authenticated mentors who have an accepted mentorship request.
    """
    user_id = int(get_jwt_identity())
    mentor_prof = MentorProfile.query.filter_by(user_id=user_id).first()
    if not mentor_prof:
        return jsonify({"status": "error", "message": "Mentor profile not found"}), 403

    mentee_prof = MenteeProfile.query.get(mentee_id)
    if not mentee_prof:
        mentee_prof = MenteeProfile.query.filter_by(user_id=mentee_id).first()

    if not mentee_prof:
        return jsonify({"status": "error", "message": f"Mentee profile with ID {mentee_id} not found"}), 404

    active_request = MentorshipRequest.query.filter_by(
        mentor_id=mentor_prof.id,
        mentee_id=mentee_prof.id,
        status='accepted'
    ).first()

    if not active_request:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you do not have an accepted mentorship with this mentee"
        }), 403

    records = AcademicRecord.query.filter_by(
        mentee_id=mentee_prof.id
    ).order_by(AcademicRecord.semester.asc()).all()

    cgpa = calculate_cgpa(records)
    records_data = [format_academic_record(r) for r in records]
    mentee_user = mentee_prof.user

    return jsonify({
        "status": "success",
        "mentee": {
            "id": mentee_prof.id,
            "user_id": mentee_prof.user_id,
            "name": mentee_user.name if mentee_user else f"Mentee #{mentee_prof.id}",
            "email": mentee_user.email if mentee_user else "",
            "profile_picture": mentee_user.profile_picture if mentee_user else None
        },
        "count": len(records_data),
        "cgpa": cgpa,
        "cgpa_label": "Calculated CGPA (Simple Average)",
        "records": records_data
    }), 200
