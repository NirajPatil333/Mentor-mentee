"""
Session management API routes.
Supports scheduling, retrieving, updating, and cancelling mentoring sessions
integrated with Jitsi Meet video rooms.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Session, MentorshipRequest, MentorProfile, MenteeProfile
from services.jitsi_service import generate_meeting_room, get_meeting_url

sessions_bp = Blueprint('sessions', __name__)

VALID_SESSION_STATUSES = {'scheduled', 'completed', 'cancelled'}


def parse_date_str(date_str: str):
    """
    Parses a date string in 'YYYY-MM-DD' format.
    Returns None if invalid.
    """
    if not isinstance(date_str, str):
        return None
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def parse_time_str(time_str: str):
    """
    Parses a time string in 'HH:MM' or 'HH:MM:SS' format.
    Returns None if invalid.
    """
    if not isinstance(time_str, str):
        return None
    for fmt in ('%H:%M:%S', '%H:%M'):
        try:
            return datetime.strptime(time_str.strip(), fmt).time()
        except ValueError:
            continue
    return None


def format_session(session: Session) -> dict:
    """
    Formats a Session model instance into a JSON dictionary including participant details
    and a ready-to-use Jitsi meeting URL.
    """
    mentor_prof = session.mentor
    mentor_user = mentor_prof.user if mentor_prof else None

    mentee_prof = session.mentee
    mentee_user = mentee_prof.user if mentee_prof else None

    return {
        "id": session.id,
        "request_id": session.request_id,
        "mentor_id": session.mentor_id,
        "mentee_id": session.mentee_id,
        "title": session.title,
        "description": session.description or "",
        "scheduled_date": session.scheduled_date.isoformat() if session.scheduled_date else None,
        "start_time": session.start_time.strftime('%H:%M:%S') if session.start_time else None,
        "end_time": session.end_time.strftime('%H:%M:%S') if session.end_time else None,
        "meeting_room": session.meeting_room,
        "meeting_url": get_meeting_url(session.meeting_room) if session.meeting_room else None,
        "status": session.status,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "mentor": {
            "id": mentor_prof.id if mentor_prof else None,
            "user_id": mentor_prof.user_id if mentor_prof else None,
            "name": mentor_user.name if mentor_user else "",
            "email": mentor_user.email if mentor_user else ""
        },
        "mentee": {
            "id": mentee_prof.id if mentee_prof else None,
            "user_id": mentee_prof.user_id if mentee_prof else None,
            "name": mentee_user.name if mentee_user else "",
            "email": mentee_user.email if mentee_user else ""
        }
    }


def is_user_participant(user_id: int, session: Session) -> bool:
    """
    Checks if the user is either the mentor or the mentee of the session.
    """
    mentor_user_id = session.mentor.user_id if (session.mentor and session.mentor.user) else None
    mentee_user_id = session.mentee.user_id if (session.mentee and session.mentee.user) else None
    return user_id in (mentor_user_id, mentee_user_id)


@sessions_bp.route('', methods=['POST'])
@sessions_bp.route('/', methods=['POST'])
@jwt_required()
def create_session():
    """
    Creates a new mentorship session for an accepted mentorship request.
    Can be created by either the mentor or mentee associated with the request.
    Generates a unique Jitsi Meet room.
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Invalid JSON body or empty request"
        }), 400

    request_id_raw = data.get('request_id')
    title = data.get('title')
    scheduled_date_raw = data.get('scheduled_date')
    start_time_raw = data.get('start_time')
    end_time_raw = data.get('end_time')
    description = data.get('description', '')

    # Validate required fields
    if request_id_raw is None:
        return jsonify({"status": "error", "message": "request_id is required"}), 400
    if not title or not isinstance(title, str) or not title.strip():
        return jsonify({"status": "error", "message": "title is required"}), 400
    if not scheduled_date_raw:
        return jsonify({"status": "error", "message": "scheduled_date is required"}), 400
    if not start_time_raw or not end_time_raw:
        return jsonify({"status": "error", "message": "start_time and end_time are required"}), 400

    try:
        request_id = int(request_id_raw)
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "request_id must be an integer"}), 400

    # Look up mentorship request
    req = MentorshipRequest.query.get(request_id)
    if not req:
        return jsonify({"status": "error", "message": f"Mentorship request {request_id} not found"}), 404

    # Verify request status is accepted
    if req.status != 'accepted':
        return jsonify({
            "status": "error",
            "message": f"Session can only be scheduled for accepted mentorship requests. Current status: '{req.status}'"
        }), 400

    # Verify authenticated user is a participant of this mentorship request
    req_mentor_user_id = req.mentor.user_id if (req.mentor and req.mentor.user) else None
    req_mentee_user_id = req.mentee.user_id if (req.mentee and req.mentee.user) else None

    if user_id not in (req_mentor_user_id, req_mentee_user_id):
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you are not a participant in this mentorship request"
        }), 403

    # Parse and validate dates and times
    scheduled_date = parse_date_str(scheduled_date_raw)
    if not scheduled_date:
        return jsonify({
            "status": "error",
            "message": "Invalid scheduled_date format. Expected 'YYYY-MM-DD'"
        }), 400

    start_time = parse_time_str(start_time_raw)
    end_time = parse_time_str(end_time_raw)
    if not start_time or not end_time:
        return jsonify({
            "status": "error",
            "message": "Invalid time format for start_time or end_time. Expected 'HH:MM' or 'HH:MM:SS'"
        }), 400

    if start_time >= end_time:
        return jsonify({
            "status": "error",
            "message": "end_time must be strictly later than start_time"
        }), 400

    # Generate unique Jitsi room name
    meeting_room = generate_meeting_room(req.id)

    try:
        new_session = Session(
            request_id=req.id,
            mentor_id=req.mentor_id,
            mentee_id=req.mentee_id,
            title=title.strip()[:150],
            description=description.strip() if isinstance(description, str) else None,
            scheduled_date=scheduled_date,
            start_time=start_time,
            end_time=end_time,
            meeting_room=meeting_room,
            status='scheduled'
        )
        db.session.add(new_session)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Session scheduled successfully",
            "session": format_session(new_session)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to schedule session: {str(e)}"
        }), 500


@sessions_bp.route('', methods=['GET'])
@sessions_bp.route('/', methods=['GET'])
@jwt_required()
def get_sessions():
    """
    Retrieves all mentorship sessions for the authenticated user (as mentor or mentee).
    """
    user_id = int(get_jwt_identity())
    mentor_prof = MentorProfile.query.filter_by(user_id=user_id).first()
    mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()

    filters = []
    if mentor_prof:
        filters.append(Session.mentor_id == mentor_prof.id)
    if mentee_prof:
        filters.append(Session.mentee_id == mentee_prof.id)

    if not filters:
        return jsonify({
            "status": "success",
            "count": 0,
            "sessions": []
        }), 200

    sessions = Session.query.filter(db.or_(*filters)).order_by(
        Session.scheduled_date.asc(), Session.start_time.asc()
    ).all()

    sessions_data = [format_session(s) for s in sessions]

    return jsonify({
        "status": "success",
        "count": len(sessions_data),
        "sessions": sessions_data
    }), 200


@sessions_bp.route('/<int:session_id>', methods=['GET'])
@jwt_required()
def get_session(session_id: int):
    """
    Retrieves detailed information for a specific session.
    Restricted to session participants.
    """
    user_id = int(get_jwt_identity())
    session = Session.query.get(session_id)
    if not session:
        return jsonify({
            "status": "error",
            "message": f"Session {session_id} not found"
        }), 404

    if not is_user_participant(user_id, session):
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you are not a participant in this session"
        }), 403

    return jsonify({
        "status": "success",
        "session": format_session(session)
    }), 200


@sessions_bp.route('/<int:session_id>', methods=['PUT'])
@jwt_required()
def update_session(session_id: int):
    """
    Updates session details (title, description, date, start_time, end_time, status).
    Restricted to session participants.
    """
    user_id = int(get_jwt_identity())
    session = Session.query.get(session_id)
    if not session:
        return jsonify({
            "status": "error",
            "message": f"Session {session_id} not found"
        }), 404

    if not is_user_participant(user_id, session):
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you are not a participant in this session"
        }), 403

    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Invalid JSON body or empty request"
        }), 400

    # Update title
    if 'title' in data:
        title = data['title']
        if not title or not isinstance(title, str) or not title.strip():
            return jsonify({"status": "error", "message": "Title cannot be empty"}), 400
        session.title = title.strip()[:150]

    # Update description
    if 'description' in data:
        desc = data['description']
        session.description = desc.strip() if isinstance(desc, str) else None

    # Update scheduled_date
    if 'scheduled_date' in data:
        parsed_date = parse_date_str(data['scheduled_date'])
        if not parsed_date:
            return jsonify({
                "status": "error",
                "message": "Invalid scheduled_date format. Expected 'YYYY-MM-DD'"
            }), 400
        session.scheduled_date = parsed_date

    # Update time range
    new_start_time = parse_time_str(data['start_time']) if 'start_time' in data else session.start_time
    new_end_time = parse_time_str(data['end_time']) if 'end_time' in data else session.end_time

    if 'start_time' in data and not new_start_time:
        return jsonify({"status": "error", "message": "Invalid start_time format"}), 400
    if 'end_time' in data and not new_end_time:
        return jsonify({"status": "error", "message": "Invalid end_time format"}), 400

    if new_start_time >= new_end_time:
        return jsonify({
            "status": "error",
            "message": "end_time must be strictly later than start_time"
        }), 400

    session.start_time = new_start_time
    session.end_time = new_end_time

    # Update status
    if 'status' in data:
        new_status = str(data['status']).strip().lower()
        if new_status not in VALID_SESSION_STATUSES:
            return jsonify({
                "status": "error",
                "message": f"Invalid status '{new_status}'. Allowed statuses: {sorted(list(VALID_SESSION_STATUSES))}"
            }), 400
        session.status = new_status

    try:
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Session updated successfully",
            "session": format_session(session)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to update session: {str(e)}"
        }), 500


@sessions_bp.route('/<int:session_id>', methods=['DELETE'])
@jwt_required()
def delete_session(session_id: int):
    """
    Cancels a session by updating its status to 'cancelled'.
    Restricted to session participants.
    """
    user_id = int(get_jwt_identity())
    session = Session.query.get(session_id)
    if not session:
        return jsonify({
            "status": "error",
            "message": f"Session {session_id} not found"
        }), 404

    if not is_user_participant(user_id, session):
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you are not a participant in this session"
        }), 403

    try:
        session.status = 'cancelled'
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Session cancelled successfully",
            "session": format_session(session)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to cancel session: {str(e)}"
        }), 500
