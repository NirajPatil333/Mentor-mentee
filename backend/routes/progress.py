"""
Progress tracking API endpoints.
Supports milestone and goal management, completion percentages, status tracking,
and mentor-mentee scoped progress authorization.
"""

from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Progress, MentorProfile, MenteeProfile, MentorshipRequest, Skill, User
from utils.auth import mentor_required, mentee_required

progress_bp = Blueprint('progress', __name__)

VALID_STATUSES = {'not_started', 'in_progress', 'completed'}


def format_progress(p: Progress) -> dict:
    """
    Formats a Progress model instance into a JSON dictionary with associated
    mentor, mentee, and skill metadata.
    """
    mentor_prof = p.mentor
    mentor_user = mentor_prof.user if mentor_prof else None
    mentee_prof = p.mentee
    mentee_user = mentee_prof.user if mentee_prof else None
    skill_obj = p.skill

    return {
        "id": p.id,
        "mentee_id": p.mentee_id,
        "mentor_id": p.mentor_id,
        "skill_id": p.skill_id,
        "goal": p.goal,
        "description": p.description or "",
        "progress_percentage": p.progress_percentage,
        "status": p.status,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        "skill": {
            "id": skill_obj.id if skill_obj else None,
            "name": skill_obj.name if skill_obj else "",
            "category": skill_obj.category if skill_obj else ""
        } if skill_obj else None,
        "mentor": {
            "id": mentor_prof.id if mentor_prof else None,
            "user_id": mentor_prof.user_id if mentor_prof else None,
            "name": mentor_user.name if mentor_user else "",
            "email": mentor_user.email if mentor_user else ""
        } if mentor_prof else None,
        "mentee": {
            "id": mentee_prof.id if mentee_prof else None,
            "user_id": mentee_prof.user_id if mentee_prof else None,
            "name": mentee_user.name if mentee_user else "",
            "email": mentee_user.email if mentee_user else ""
        } if mentee_prof else None
    }


@progress_bp.route('', methods=['GET'])
@progress_bp.route('/', methods=['GET'])
@jwt_required()
def get_progress():
    """
    Retrieves progress records visible to the authenticated user:
    - Mentors view progress records they have created/managed.
    - Mentees view progress records assigned to them.
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    if user.role == 'mentor':
        mentor_prof = MentorProfile.query.filter_by(user_id=user_id).first()
        if not mentor_prof:
            return jsonify({"status": "success", "count": 0, "progress": []}), 200

        records = Progress.query.filter_by(
            mentor_id=mentor_prof.id
        ).order_by(Progress.updated_at.desc()).all()

    elif user.role == 'mentee':
        mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()
        if not mentee_prof:
            return jsonify({"status": "success", "count": 0, "progress": []}), 200

        records = Progress.query.filter_by(
            mentee_id=mentee_prof.id
        ).order_by(Progress.updated_at.desc()).all()

    else:
        return jsonify({"status": "error", "message": "Invalid user role"}), 403

    records_data = [format_progress(r) for r in records]
    return jsonify({
        "status": "success",
        "count": len(records_data),
        "progress": records_data
    }), 200


@progress_bp.route('/mentees', methods=['GET'])
@mentor_required
def get_mentor_mentees():
    """
    Retrieves accepted mentees for the authenticated mentor to populate
    mentee selection dropdowns in the progress tracking interface.
    """
    user_id = int(get_jwt_identity())
    mentor_prof = MentorProfile.query.filter_by(user_id=user_id).first()
    if not mentor_prof:
        return jsonify({"status": "success", "mentees": []}), 200

    accepted_requests = MentorshipRequest.query.filter_by(
        mentor_id=mentor_prof.id,
        status='accepted'
    ).all()

    mentees = []
    seen = set()
    for req in accepted_requests:
        mentee_prof = req.mentee
        if mentee_prof and mentee_prof.id not in seen:
            seen.add(mentee_prof.id)
            mentee_user = mentee_prof.user
            mentees.append({
                "id": mentee_prof.id,
                "user_id": mentee_prof.user_id,
                "name": mentee_user.name if mentee_user else f"Mentee #{mentee_prof.id}",
                "email": mentee_user.email if mentee_user else ""
            })

    return jsonify({
        "status": "success",
        "mentees": mentees
    }), 200


@progress_bp.route('', methods=['POST'])
@progress_bp.route('/', methods=['POST'])
@mentor_required
def create_progress():
    """
    Creates a new progress record for an accepted mentee.
    Restricted to authenticated mentors with an active accepted mentorship.
    """
    user_id = int(get_jwt_identity())
    mentor_prof = MentorProfile.query.filter_by(user_id=user_id).first()
    if not mentor_prof:
        mentor_prof = MentorProfile(user_id=user_id)
        db.session.add(mentor_prof)
        db.session.commit()

    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Invalid JSON body or empty request"
        }), 400

    mentee_id_raw = data.get('mentee_id')
    skill_id_raw = data.get('skill_id')
    goal = data.get('goal')
    description = data.get('description', '')
    progress_percentage_raw = data.get('progress_percentage', 0)
    status_raw = data.get('status', 'not_started')

    # Validate mentee_id
    if mentee_id_raw is None:
        return jsonify({"status": "error", "message": "mentee_id is required"}), 400
    try:
        mentee_id = int(mentee_id_raw)
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "mentee_id must be a valid integer"}), 400

    mentee_prof = MenteeProfile.query.get(mentee_id)
    if not mentee_prof:
        mentee_prof = MenteeProfile.query.filter_by(user_id=mentee_id).first()
    if not mentee_prof:
        return jsonify({"status": "error", "message": f"Mentee profile with ID {mentee_id} not found"}), 404

    # Verify accepted mentorship relationship
    rel = MentorshipRequest.query.filter_by(
        mentor_id=mentor_prof.id,
        mentee_id=mentee_prof.id,
        status='accepted'
    ).first()

    if not rel:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you can only track progress for mentees with whom you have an accepted mentorship"
        }), 403

    # Validate skill_id
    if skill_id_raw is None:
        return jsonify({"status": "error", "message": "skill_id is required"}), 400
    try:
        skill_id = int(skill_id_raw)
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "skill_id must be a valid integer"}), 400

    skill_obj = Skill.query.get(skill_id)
    if not skill_obj:
        return jsonify({"status": "error", "message": f"Skill with ID {skill_id} not found"}), 404

    # Validate goal
    if not goal or not isinstance(goal, str) or not goal.strip():
        return jsonify({"status": "error", "message": "Learning goal title is required"}), 400
    clean_goal = goal.strip()[:255]

    # Validate progress_percentage
    try:
        progress_percentage = int(progress_percentage_raw)
        if progress_percentage < 0 or progress_percentage > 100:
            raise ValueError()
    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": "progress_percentage must be an integer between 0 and 100"
        }), 400

    # Validate status
    status = str(status_raw).strip().lower()
    if status not in VALID_STATUSES:
        return jsonify({
            "status": "error",
            "message": f"Invalid status '{status}'. Allowed values: {sorted(list(VALID_STATUSES))}"
        }), 400

    try:
        new_progress = Progress(
            mentor_id=mentor_prof.id,
            mentee_id=mentee_prof.id,
            skill_id=skill_obj.id,
            goal=clean_goal,
            description=description.strip() if isinstance(description, str) and description.strip() else None,
            progress_percentage=progress_percentage,
            status=status,
            updated_at=datetime.now(timezone.utc)
        )
        db.session.add(new_progress)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Progress record created successfully",
            "progress": format_progress(new_progress)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to create progress record: {str(e)}"
        }), 500


@progress_bp.route('/<int:progress_id>', methods=['PUT'])
@mentor_required
def update_progress(progress_id: int):
    """
    Updates an existing progress record.
    Restricted to the creator mentor.
    """
    user_id = int(get_jwt_identity())
    mentor_prof = MentorProfile.query.filter_by(user_id=user_id).first()
    if not mentor_prof:
        return jsonify({"status": "error", "message": "Mentor profile not found"}), 404

    record = Progress.query.get(progress_id)
    if not record:
        return jsonify({"status": "error", "message": f"Progress record {progress_id} not found"}), 404

    if record.mentor_id != mentor_prof.id:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you can only update progress records you manage"
        }), 403

    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Invalid JSON body or empty request"
        }), 400

    # Optional goal update
    if 'goal' in data:
        goal = data['goal']
        if not goal or not isinstance(goal, str) or not goal.strip():
            return jsonify({"status": "error", "message": "Goal cannot be empty"}), 400
        record.goal = goal.strip()[:255]

    # Optional description update
    if 'description' in data:
        desc = data['description']
        record.description = desc.strip() if isinstance(desc, str) and desc.strip() else None

    # Optional skill update
    if 'skill_id' in data:
        try:
            skill_id = int(data['skill_id'])
            skill_obj = Skill.query.get(skill_id)
            if not skill_obj:
                return jsonify({"status": "error", "message": f"Skill {skill_id} not found"}), 404
            record.skill_id = skill_obj.id
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "skill_id must be a valid integer"}), 400

    # Optional progress_percentage update
    if 'progress_percentage' in data:
        try:
            pct = int(data['progress_percentage'])
            if pct < 0 or pct > 100:
                raise ValueError()
            record.progress_percentage = pct
        except (ValueError, TypeError):
            return jsonify({
                "status": "error",
                "message": "progress_percentage must be an integer between 0 and 100"
            }), 400

    # Optional status update
    if 'status' in data:
        status = str(data['status']).strip().lower()
        if status not in VALID_STATUSES:
            return jsonify({
                "status": "error",
                "message": f"Invalid status '{status}'. Allowed values: {sorted(list(VALID_STATUSES))}"
            }), 400
        record.status = status

    record.updated_at = datetime.now(timezone.utc)

    try:
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Progress record updated successfully",
            "progress": format_progress(record)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to update progress record: {str(e)}"
        }), 500


@progress_bp.route('/<int:progress_id>', methods=['DELETE'])
@mentor_required
def delete_progress(progress_id: int):
    """
    Deletes a progress record.
    Restricted to the creator mentor.
    """
    user_id = int(get_jwt_identity())
    mentor_prof = MentorProfile.query.filter_by(user_id=user_id).first()
    if not mentor_prof:
        return jsonify({"status": "error", "message": "Mentor profile not found"}), 404

    record = Progress.query.get(progress_id)
    if not record:
        return jsonify({"status": "error", "message": f"Progress record {progress_id} not found"}), 404

    if record.mentor_id != mentor_prof.id:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you can only delete progress records you manage"
        }), 403

    try:
        db.session.delete(record)
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Progress record deleted successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to delete progress record: {str(e)}"
        }), 500
