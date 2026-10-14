"""
Session management API routes.
Supports scheduling, retrieving, updating, and cancelling mentoring sessions
integrated with Jitsi Meet video rooms.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Session, MentorshipRequest, MentorProfile, MenteeProfile, User, SessionParticipant
from utils.auth import get_email_domain
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
    Formats a Session model instance into a JSON dictionary including all participant details
    and a ready-to-use Jitsi meeting URL.
    """
    mentor_prof = session.mentor
    mentor_user = mentor_prof.user if mentor_prof else None

    # Resolve all participants from session_participants
    participants_data = []
    seen_mentee_ids = set()

    for p in session.participants:
        mp = p.mentee
        if mp and mp.user:
            seen_mentee_ids.add(mp.id)
            participants_data.append({
                "id": mp.id,
                "user_id": mp.user_id,
                "name": mp.user.name or "",
                "email": mp.user.email or "",
                "domain": get_email_domain(mp.user.email),
                "joined_at": p.joined_at.isoformat() if p.joined_at else None
            })

    # Backward compatibility: include primary mentee if not already listed
    primary_mentee_prof = session.mentee
    primary_mentee_user = primary_mentee_prof.user if primary_mentee_prof else None
    if primary_mentee_prof and primary_mentee_prof.id not in seen_mentee_ids:
        participants_data.insert(0, {
            "id": primary_mentee_prof.id,
            "user_id": primary_mentee_prof.user_id,
            "name": primary_mentee_user.name if primary_mentee_user else "",
            "email": primary_mentee_user.email if primary_mentee_user else "",
            "domain": get_email_domain(primary_mentee_user.email) if primary_mentee_user else "",
            "joined_at": session.created_at.isoformat() if session.created_at else None
        })

    # Domain for this session (derived from participants or primary mentee)
    session_domain = ""
    if participants_data:
        session_domain = participants_data[0].get("domain") or ""
    elif primary_mentee_user and primary_mentee_user.email:
        session_domain = get_email_domain(primary_mentee_user.email)

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
        "domain": session_domain,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "mentor": {
            "id": mentor_prof.id if mentor_prof else None,
            "user_id": mentor_prof.user_id if mentor_prof else None,
            "name": mentor_user.name if mentor_user else "",
            "email": mentor_user.email if mentor_user else ""
        },
        "mentee": {
            "id": primary_mentee_prof.id if primary_mentee_prof else None,
            "user_id": primary_mentee_prof.user_id if primary_mentee_prof else None,
            "name": primary_mentee_user.name if primary_mentee_user else "",
            "email": primary_mentee_user.email if primary_mentee_user else ""
        },
        "participants": participants_data
    }


def is_user_participant(user_id: int, session: Session) -> bool:
    """
    Checks if the user is either the mentor or one of the mentees of the session.
    """
    mentor_user_id = session.mentor.user_id if (session.mentor and session.mentor.user) else None
    if user_id == mentor_user_id:
        return True

    # Check primary mentee
    primary_mentee_user_id = session.mentee.user_id if (session.mentee and session.mentee.user) else None
    if user_id == primary_mentee_user_id:
        return True

    # Check all session participants
    for p in session.participants:
        if p.mentee and p.mentee.user_id == user_id:
            return True

    return False


@sessions_bp.route('', methods=['POST'])
@sessions_bp.route('/', methods=['POST'])
@jwt_required()
def create_session():
    """
    Creates a new mentorship session for an accepted mentorship request.
    Can be created by either the mentor or mentee associated with the request.
    Optionally accepts additional_mentee_ids for multi-mentee sessions from the same domain.
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
    additional_mentee_ids = data.get('additional_mentee_ids', [])

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

    # Primary mentee domain
    primary_mentee_domain = get_email_domain(req.mentee.user.email) if (req.mentee and req.mentee.user) else ""

    # Validate additional mentees if provided
    mentees_to_add = [req.mentee_id]
    if additional_mentee_ids:
        if not isinstance(additional_mentee_ids, list):
            return jsonify({"status": "error", "message": "additional_mentee_ids must be a list"}), 400

        for mid in additional_mentee_ids:
            try:
                mid_int = int(mid)
            except (ValueError, TypeError):
                return jsonify({"status": "error", "message": f"Invalid mentee ID: {mid}"}), 400

            if mid_int in mentees_to_add:
                continue

            # Must be an accepted mentee of this mentor
            acc_req = MentorshipRequest.query.filter_by(
                mentor_id=req.mentor_id,
                mentee_id=mid_int,
                status='accepted'
            ).first()
            if not acc_req:
                return jsonify({
                    "status": "error",
                    "message": f"Mentee ID {mid_int} does not have an accepted mentorship with this mentor"
                }), 400

            # Enforce domain eligibility
            extra_mentee_domain = get_email_domain(acc_req.mentee.user.email)
            if extra_mentee_domain != primary_mentee_domain:
                return jsonify({
                    "status": "error",
                    "message": f"Domain mismatch: mentee {acc_req.mentee.user.name} ({extra_mentee_domain}) does not match session domain ({primary_mentee_domain})"
                }), 400

            mentees_to_add.append(mid_int)

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
        db.session.flush()

        # Add all mentees to session_participants
        for mid in mentees_to_add:
            sp = SessionParticipant(
                session_id=new_session.id,
                mentee_id=mid
            )
            db.session.add(sp)

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
    Retrieves all mentorship sessions for the authenticated user (as mentor or participating mentee).
    """
    user_id = int(get_jwt_identity())
    mentor_prof = MentorProfile.query.filter_by(user_id=user_id).first()
    mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()

    session_ids = set()

    if mentor_prof:
        mentor_sess = Session.query.filter_by(mentor_id=mentor_prof.id).all()
        for s in mentor_sess:
            session_ids.add(s.id)

    if mentee_prof:
        # Check sessions where mentee is primary
        primary_sess = Session.query.filter_by(mentee_id=mentee_prof.id).all()
        for s in primary_sess:
            session_ids.add(s.id)

        # Check sessions where mentee is in session_participants
        participations = SessionParticipant.query.filter_by(mentee_id=mentee_prof.id).all()
        for p in participations:
            session_ids.add(p.session_id)

    if not session_ids:
        return jsonify({
            "status": "success",
            "count": 0,
            "sessions": []
        }), 200

    sessions = Session.query.filter(Session.id.in_(list(session_ids))).order_by(
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


@sessions_bp.route('/<int:session_id>/participants', methods=['POST'])
@jwt_required()
def add_participant(session_id: int):
    """
    Adds an eligible mentee from the same domain to an existing session.
    Restricted to session mentor or authorized session participant.
    """
    user_id = int(get_jwt_identity())
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"status": "error", "message": f"Session {session_id} not found"}), 404

    # Authorization: user must be mentor of this session
    mentor_user_id = session.mentor.user_id if (session.mentor and session.mentor.user) else None
    if user_id != mentor_user_id:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: only the session mentor can invite additional mentees"
        }), 403

    data = request.get_json(silent=True) or {}
    mentee_id_raw = data.get('mentee_id')
    if mentee_id_raw is None:
        return jsonify({"status": "error", "message": "mentee_id is required"}), 400

    try:
        target_mentee_id = int(mentee_id_raw)
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "mentee_id must be an integer"}), 400

    # Mentee profile check
    target_mentee = MenteeProfile.query.get(target_mentee_id)
    if not target_mentee or not target_mentee.user:
        return jsonify({"status": "error", "message": f"Mentee profile {target_mentee_id} not found"}), 404

    # Mentorship status check: target mentee must have an accepted mentorship request with this mentor
    acc_req = MentorshipRequest.query.filter_by(
        mentor_id=session.mentor_id,
        mentee_id=target_mentee_id,
        status='accepted'
    ).first()
    if not acc_req:
        return jsonify({
            "status": "error",
            "message": "Mentee must have an accepted mentorship relationship with the mentor"
        }), 400

    # Domain eligibility check
    primary_mentee_user = session.mentee.user if (session.mentee and session.mentee.user) else None
    primary_domain = get_email_domain(primary_mentee_user.email) if primary_mentee_user else ""
    target_domain = get_email_domain(target_mentee.user.email)

    if target_domain != primary_domain:
        return jsonify({
            "status": "error",
            "message": f"Domain mismatch: mentee ({target_domain}) must belong to the session domain ({primary_domain})"
        }), 400

    # Check if already a participant
    existing_p = SessionParticipant.query.filter_by(
        session_id=session.id,
        mentee_id=target_mentee_id
    ).first()
    if existing_p or session.mentee_id == target_mentee_id:
        return jsonify({
            "status": "error",
            "message": "Mentee is already a participant in this session"
        }), 409

    try:
        new_p = SessionParticipant(
            session_id=session.id,
            mentee_id=target_mentee_id
        )
        db.session.add(new_p)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": f"Mentee {target_mentee.user.name} added to session successfully",
            "session": format_session(session)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to add mentee to session: {str(e)}"
        }), 500


@sessions_bp.route('/<int:session_id>/available-mentees', methods=['GET'])
@jwt_required()
def get_available_mentees(session_id: int):
    """
    Returns eligible mentees (from the same domain with accepted mentorship)
    who have not yet joined this session.
    """
    user_id = int(get_jwt_identity())
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"status": "error", "message": f"Session {session_id} not found"}), 404

    mentor_user_id = session.mentor.user_id if (session.mentor and session.mentor.user) else None
    if user_id != mentor_user_id:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: only the session mentor can view available mentees"
        }), 403

    primary_mentee_user = session.mentee.user if (session.mentee and session.mentee.user) else None
    primary_domain = get_email_domain(primary_mentee_user.email) if primary_mentee_user else ""

    # Already participating mentee IDs
    participating_mentee_ids = {session.mentee_id}
    for p in session.participants:
        participating_mentee_ids.add(p.mentee_id)

    # Find all accepted mentees for this mentor
    accepted_requests = MentorshipRequest.query.filter_by(
        mentor_id=session.mentor_id,
        status='accepted'
    ).all()

    eligible_mentees = []
    for req in accepted_requests:
        m = req.mentee
        if not m or not m.user:
            continue
        if m.id in participating_mentee_ids:
            continue
        m_domain = get_email_domain(m.user.email)
        if m_domain == primary_domain:
            eligible_mentees.append({
                "id": m.id,
                "user_id": m.user_id,
                "name": m.user.name,
                "email": m.user.email,
                "domain": m_domain,
                "request_id": req.id
            })

    return jsonify({
        "status": "success",
        "domain": primary_domain,
        "count": len(eligible_mentees),
        "mentees": eligible_mentees
    }), 200
