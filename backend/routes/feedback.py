"""
Feedback and Rating API endpoints.
Provides session feedback submission for mentees and rating analytics/reviews for mentors.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from extensions import db
from models import Feedback, Session, MentorProfile, MenteeProfile, User
from utils.auth import mentee_required, mentor_required

feedback_bp = Blueprint('feedback', __name__)


@feedback_bp.route('', methods=['POST'])
@mentee_required
def submit_feedback():
    """
    Submits feedback and a rating (1-5) for a completed session.
    Only authenticated mentees can submit feedback for sessions they participated in.
    Recalculates the mentor's average rating and total review count upon submission.
    """
    user_id = int(get_jwt_identity())
    mentee_profile = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not mentee_profile:
        return jsonify({
            "status": "error",
            "message": "Mentee profile not found"
        }), 404

    data = request.get_json(silent=True) or {}

    session_id = data.get('session_id')
    if not session_id or isinstance(session_id, bool) or not isinstance(session_id, int):
        return jsonify({
            "status": "error",
            "message": "session_id is required and must be an integer"
        }), 400

    session = db.session.get(Session, session_id)
    if not session:
        return jsonify({
            "status": "error",
            "message": "Session not found"
        }), 404

    # Ownership check: mentee must be part of this session
    if session.mentee_id != mentee_profile.id:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: session does not belong to you"
        }), 403

    # Rating validation: integer strictly between 1 and 5
    rating = data.get('rating')
    if rating is None or isinstance(rating, bool) or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({
            "status": "error",
            "message": "rating is required and must be an integer between 1 and 5"
        }), 400

    comment = data.get('comment')
    if comment is not None:
        comment = str(comment).strip()

    # Prevent duplicate feedback for the same session by the same mentee
    existing_feedback = Feedback.query.filter_by(
        session_id=session.id,
        mentee_id=mentee_profile.id
    ).first()
    if existing_feedback:
        return jsonify({
            "status": "error",
            "message": "Feedback has already been submitted for this session"
        }), 400

    # Derive mentor_id from session (do not trust frontend)
    mentor_id = session.mentor_id

    try:
        feedback = Feedback(
            session_id=session.id,
            mentor_id=mentor_id,
            mentee_id=mentee_profile.id,
            rating=rating,
            comment=comment
        )
        db.session.add(feedback)
        db.session.flush()

        # Recalculate mentor's average rating and total reviews from actual feedback records
        mentor_feedbacks = Feedback.query.filter_by(mentor_id=mentor_id).all()
        total_reviews = len(mentor_feedbacks)
        if total_reviews > 0:
            avg_rating = round(sum(f.rating for f in mentor_feedbacks) / total_reviews, 2)
        else:
            avg_rating = 0.0

        mentor_profile = db.session.get(MentorProfile, mentor_id)
        if mentor_profile:
            mentor_profile.total_reviews = total_reviews
            mentor_profile.average_rating = avg_rating

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Feedback submitted successfully",
            "feedback": {
                "id": feedback.id,
                "session_id": feedback.session_id,
                "mentor_id": feedback.mentor_id,
                "mentee_id": feedback.mentee_id,
                "rating": feedback.rating,
                "comment": feedback.comment,
                "created_at": feedback.created_at.isoformat() if feedback.created_at else None
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to submit feedback: {str(e)}"
        }), 500


@feedback_bp.route('/mentee', methods=['GET'])
@mentee_required
def get_mentee_feedback():
    """
    Retrieves all session feedback submitted by the authenticated mentee.
    """
    user_id = int(get_jwt_identity())
    mentee_profile = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not mentee_profile:
        return jsonify({
            "status": "success",
            "feedbacks": []
        }), 200

    feedbacks = Feedback.query.filter_by(mentee_id=mentee_profile.id).order_by(Feedback.created_at.desc()).all()

    results = []
    for fb in feedbacks:
        mentor_name = ""
        if fb.mentor and fb.mentor.user:
            mentor_name = fb.mentor.user.name

        session_title = fb.session.title if fb.session else ""
        session_date = fb.session.scheduled_date.strftime('%Y-%m-%d') if fb.session and fb.session.scheduled_date else ""

        results.append({
            "id": fb.id,
            "session_id": fb.session_id,
            "session_title": session_title,
            "session_date": session_date,
            "mentor_id": fb.mentor_id,
            "mentor_name": mentor_name,
            "rating": fb.rating,
            "comment": fb.comment or "",
            "created_at": fb.created_at.isoformat() if fb.created_at else None
        })

    return jsonify({
        "status": "success",
        "feedbacks": results
    }), 200


@feedback_bp.route('/mentor', methods=['GET'])
@mentor_required
def get_mentor_feedback():
    """
    Retrieves all feedback/ratings received by the authenticated mentor.
    Mentors can view feedback but cannot modify or create ratings.
    """
    user_id = int(get_jwt_identity())
    mentor_profile = MentorProfile.query.filter_by(user_id=user_id).first()
    if not mentor_profile:
        return jsonify({
            "status": "success",
            "average_rating": 0.0,
            "total_reviews": 0,
            "feedbacks": []
        }), 200

    feedbacks = Feedback.query.filter_by(mentor_id=mentor_profile.id).order_by(Feedback.created_at.desc()).all()

    results = []
    for fb in feedbacks:
        mentee_name = ""
        if fb.mentee and fb.mentee.user:
            mentee_name = fb.mentee.user.name

        session_title = fb.session.title if fb.session else ""
        session_date = fb.session.scheduled_date.strftime('%Y-%m-%d') if fb.session and fb.session.scheduled_date else ""

        results.append({
            "id": fb.id,
            "session_id": fb.session_id,
            "session_title": session_title,
            "session_date": session_date,
            "mentee_id": fb.mentee_id,
            "mentee_name": mentee_name,
            "rating": fb.rating,
            "comment": fb.comment or "",
            "created_at": fb.created_at.isoformat() if fb.created_at else None
        })

    return jsonify({
        "status": "success",
        "average_rating": mentor_profile.average_rating or 0.0,
        "total_reviews": mentor_profile.total_reviews or 0,
        "feedbacks": results
    }), 200
