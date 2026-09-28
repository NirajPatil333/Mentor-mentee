"""
Mentorship requests API endpoints.
Manages creation, retrieval, and status updates (accept/reject) for mentorship requests.
"""

from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from extensions import db
from models import MentorshipRequest, MentorProfile, MenteeProfile
from utils.auth import mentee_required, mentor_required

requests_bp = Blueprint('requests', __name__)


def format_request(req: MentorshipRequest) -> dict:
    """
    Formats a MentorshipRequest model instance into a JSON-serializable dictionary.
    Excludes any sensitive data.
    """
    return {
        "id": req.id,
        "mentee_id": req.mentee_id,
        "mentor_id": req.mentor_id,
        "message": req.message or "",
        "status": req.status,
        "requested_at": req.requested_at.isoformat() if req.requested_at else None,
        "responded_at": req.responded_at.isoformat() if req.responded_at else None
    }


@requests_bp.route('', methods=['POST'])
@requests_bp.route('/', methods=['POST'])
@mentee_required
def create_request():
    """
    Creates a new mentorship request from the authenticated mentee to a specified mentor.
    Validates mentor existence, self-request prevention, message bounds, and duplicate active requests.
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Invalid JSON body or empty request"
        }), 400

    mentor_id_raw = data.get('mentor_id')
    if mentor_id_raw is None:
        return jsonify({
            "status": "error",
            "message": "mentor_id is required"
        }), 400

    try:
        mentor_id = int(mentor_id_raw)
    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": "mentor_id must be a valid integer"
        }), 400

    # Retrieve mentor profile (check by profile ID first, then by user_id fallback)
    mentor_profile = MentorProfile.query.get(mentor_id)
    if not mentor_profile:
        mentor_profile = MentorProfile.query.filter_by(user_id=mentor_id).first()

    if not mentor_profile:
        return jsonify({
            "status": "error",
            "message": f"Mentor profile not found for ID {mentor_id}"
        }), 404

    # Ensure mentee profile exists for the current authenticated mentee user
    mentee_profile = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not mentee_profile:
        mentee_profile = MenteeProfile(user_id=user_id)
        db.session.add(mentee_profile)
        db.session.flush()

    # Prevent self-request
    if mentor_profile.user_id == user_id or mentor_profile.id == mentee_profile.id:
        return jsonify({
            "status": "error",
            "message": "Mentee cannot send a mentorship request to themselves"
        }), 400

    # Validate message length if provided
    message = data.get('message', '')
    if message is not None:
        if not isinstance(message, str):
            return jsonify({
                "status": "error",
                "message": "Message must be a string"
            }), 400
        if len(message) > 2000:
            return jsonify({
                "status": "error",
                "message": "Message exceeds maximum allowed length of 2000 characters"
            }), 400
        message = message.strip()

    # Check for existing pending or active request between this mentee and mentor
    existing_request = MentorshipRequest.query.filter_by(
        mentee_id=mentee_profile.id,
        mentor_id=mentor_profile.id
    ).filter(
        MentorshipRequest.status.in_(['pending', 'accepted'])
    ).first()

    if existing_request:
        return jsonify({
            "status": "error",
            "message": f"An active or pending mentorship request already exists with status '{existing_request.status}'"
        }), 409

    try:
        new_request = MentorshipRequest(
            mentee_id=mentee_profile.id,
            mentor_id=mentor_profile.id,
            message=message or None,
            status='pending',
            requested_at=datetime.now(timezone.utc)
        )
        db.session.add(new_request)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Mentorship request created successfully",
            "request": format_request(new_request)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to create mentorship request: {str(e)}"
        }), 500


@requests_bp.route('/sent', methods=['GET'])
@mentee_required
def get_sent_requests():
    """
    Retrieves all mentorship requests created by the authenticated mentee.
    Includes mentor details and timestamps.
    """
    user_id = int(get_jwt_identity())
    mentee_profile = MenteeProfile.query.filter_by(user_id=user_id).first()

    if not mentee_profile:
        return jsonify({
            "status": "success",
            "count": 0,
            "requests": []
        }), 200

    requests_list = MentorshipRequest.query.filter_by(
        mentee_id=mentee_profile.id
    ).order_by(
        MentorshipRequest.requested_at.desc()
    ).all()

    requests_data = []
    for req in requests_list:
        mentor_prof = req.mentor
        mentor_user = mentor_prof.user if mentor_prof else None
        item = format_request(req)
        item["mentor"] = {
            "id": mentor_prof.id if mentor_prof else None,
            "user_id": mentor_prof.user_id if mentor_prof else None,
            "name": mentor_user.name if mentor_user else "",
            "email": mentor_user.email if mentor_user else "",
            "bio": mentor_prof.bio or "" if mentor_prof else "",
            "current_position": mentor_prof.current_position or "" if mentor_prof else "",
            "experience_years": mentor_prof.experience_years or 0 if mentor_prof else 0,
            "education": mentor_prof.education or "" if mentor_prof else "",
            "availability_status": mentor_prof.availability_status or "available" if mentor_prof else "available",
            "average_rating": mentor_prof.average_rating or 0.0 if mentor_prof else 0.0,
            "total_reviews": mentor_prof.total_reviews or 0 if mentor_prof else 0
        }
        requests_data.append(item)

    return jsonify({
        "status": "success",
        "count": len(requests_data),
        "requests": requests_data
    }), 200


@requests_bp.route('/received', methods=['GET'])
@mentor_required
def get_received_requests():
    """
    Retrieves all mentorship requests received by the authenticated mentor.
    Includes mentee details and timestamps.
    """
    user_id = int(get_jwt_identity())
    mentor_profile = MentorProfile.query.filter_by(user_id=user_id).first()

    if not mentor_profile:
        return jsonify({
            "status": "success",
            "count": 0,
            "requests": []
        }), 200

    requests_list = MentorshipRequest.query.filter_by(
        mentor_id=mentor_profile.id
    ).order_by(
        MentorshipRequest.requested_at.desc()
    ).all()

    requests_data = []
    for req in requests_list:
        mentee_prof = req.mentee
        mentee_user = mentee_prof.user if mentee_prof else None
        item = format_request(req)
        item["mentee"] = {
            "id": mentee_prof.id if mentee_prof else None,
            "user_id": mentee_prof.user_id if mentee_prof else None,
            "name": mentee_user.name if mentee_user else "",
            "email": mentee_user.email if mentee_user else "",
            "bio": mentee_prof.bio or "" if mentee_prof else "",
            "education": mentee_prof.education or "" if mentee_prof else "",
            "learning_goal": mentee_prof.learning_goal or "" if mentee_prof else "",
            "experience_level": mentee_prof.experience_level or "" if mentee_prof else ""
        }
        requests_data.append(item)

    return jsonify({
        "status": "success",
        "count": len(requests_data),
        "requests": requests_data
    }), 200


@requests_bp.route('/<int:request_id>/accept', methods=['PATCH'])
@mentor_required
def accept_request(request_id: int):
    """
    Accepts a pending mentorship request.
    Restricted to the receiving mentor.
    """
    user_id = int(get_jwt_identity())
    mentor_profile = MentorProfile.query.filter_by(user_id=user_id).first()

    req = MentorshipRequest.query.get(request_id)
    if not req:
        return jsonify({
            "status": "error",
            "message": f"Mentorship request with ID {request_id} not found"
        }), 404

    if not mentor_profile or req.mentor_id != mentor_profile.id:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: request does not belong to the authenticated mentor"
        }), 403

    if req.status == 'accepted':
        return jsonify({
            "status": "success",
            "message": "Mentorship request is already accepted",
            "request": format_request(req)
        }), 200

    if req.status == 'rejected':
        return jsonify({
            "status": "error",
            "message": "Cannot accept a mentorship request that has already been rejected"
        }), 400

    if req.status != 'pending':
        return jsonify({
            "status": "error",
            "message": f"Only pending requests can be accepted. Current status: '{req.status}'"
        }), 400

    try:
        req.status = 'accepted'
        req.responded_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Mentorship request accepted successfully",
            "request": format_request(req)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to accept request: {str(e)}"
        }), 500


@requests_bp.route('/<int:request_id>/reject', methods=['PATCH'])
@mentor_required
def reject_request(request_id: int):
    """
    Rejects a pending mentorship request.
    Restricted to the receiving mentor.
    """
    user_id = int(get_jwt_identity())
    mentor_profile = MentorProfile.query.filter_by(user_id=user_id).first()

    req = MentorshipRequest.query.get(request_id)
    if not req:
        return jsonify({
            "status": "error",
            "message": f"Mentorship request with ID {request_id} not found"
        }), 404

    if not mentor_profile or req.mentor_id != mentor_profile.id:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: request does not belong to the authenticated mentor"
        }), 403

    if req.status == 'rejected':
        return jsonify({
            "status": "success",
            "message": "Mentorship request is already rejected",
            "request": format_request(req)
        }), 200

    if req.status == 'accepted':
        return jsonify({
            "status": "error",
            "message": "Cannot reject a mentorship request that has already been accepted"
        }), 400

    if req.status != 'pending':
        return jsonify({
            "status": "error",
            "message": f"Only pending requests can be rejected. Current status: '{req.status}'"
        }), 400

    try:
        req.status = 'rejected'
        req.responded_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Mentorship request rejected successfully",
            "request": format_request(req)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to reject request: {str(e)}"
        }), 500
