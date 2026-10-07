"""
Achievements management API endpoints.
Supports milestone accomplishments, awards, project highlights, and verification links.
Strictly mentee-owned with JWT authentication and isolation.
"""

from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from extensions import db
from models import Achievement, MenteeProfile, User
from utils.auth import mentee_required

achievements_bp = Blueprint('achievements', __name__)


def parse_date_str(date_str: str):
    """
    Parses a date string in 'YYYY-MM-DD' format.
    """
    if not isinstance(date_str, str):
        return None
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def format_achievement(ach: Achievement) -> dict:
    """
    Formats an Achievement model instance into a JSON-serializable dictionary.
    """
    return {
        "id": ach.id,
        "mentee_id": ach.mentee_id,
        "title": ach.title,
        "description": ach.description or "",
        "achievement_date": ach.achievement_date.isoformat() if ach.achievement_date else None,
        "achievement_url": ach.achievement_url or "",
        "created_at": ach.created_at.isoformat() if ach.created_at else None
    }


@achievements_bp.route('', methods=['GET'])
@achievements_bp.route('/', methods=['GET'])
@mentee_required
def get_achievements():
    """
    Retrieves all achievements recorded by the authenticated mentee.
    """
    user_id = int(get_jwt_identity())
    mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not mentee_prof:
        return jsonify({"status": "success", "count": 0, "achievements": []}), 200

    achievements = Achievement.query.filter_by(
        mentee_id=mentee_prof.id
    ).order_by(Achievement.achievement_date.desc(), Achievement.created_at.desc()).all()

    achievements_data = [format_achievement(a) for a in achievements]
    return jsonify({
        "status": "success",
        "count": len(achievements_data),
        "achievements": achievements_data
    }), 200


@achievements_bp.route('', methods=['POST'])
@achievements_bp.route('/', methods=['POST'])
@mentee_required
def create_achievement():
    """
    Creates a new achievement record for the authenticated mentee.
    """
    user_id = int(get_jwt_identity())
    mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not mentee_prof:
        mentee_prof = MenteeProfile(user_id=user_id)
        db.session.add(mentee_prof)
        db.session.commit()

    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Invalid JSON body or empty request"
        }), 400

    title = data.get('title')
    description = data.get('description', '')
    achievement_date_raw = data.get('achievement_date')
    achievement_url = data.get('achievement_url', '')

    if not title or not isinstance(title, str) or not title.strip():
        return jsonify({"status": "error", "message": "Achievement title is required"}), 400

    if not achievement_date_raw:
        return jsonify({"status": "error", "message": "achievement_date is required"}), 400

    achievement_date = parse_date_str(achievement_date_raw)
    if not achievement_date:
        return jsonify({
            "status": "error",
            "message": "Invalid achievement_date format. Expected 'YYYY-MM-DD'"
        }), 400

    clean_url = None
    if achievement_url and isinstance(achievement_url, str) and achievement_url.strip():
        clean_url = achievement_url.strip()[:500]

    try:
        new_achievement = Achievement(
            mentee_id=mentee_prof.id,
            title=title.strip()[:200],
            description=description.strip() if isinstance(description, str) and description.strip() else None,
            achievement_date=achievement_date,
            achievement_url=clean_url,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(new_achievement)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Achievement added successfully",
            "achievement": format_achievement(new_achievement)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to create achievement: {str(e)}"
        }), 500


@achievements_bp.route('/<int:achievement_id>', methods=['PUT'])
@mentee_required
def update_achievement(achievement_id: int):
    """
    Updates an existing achievement.
    Restricted to the owner mentee.
    """
    user_id = int(get_jwt_identity())
    mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not mentee_prof:
        return jsonify({"status": "error", "message": "Mentee profile not found"}), 404

    ach = Achievement.query.get(achievement_id)
    if not ach:
        return jsonify({"status": "error", "message": f"Achievement {achievement_id} not found"}), 404

    if ach.mentee_id != mentee_prof.id:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you can only update your own achievements"
        }), 403

    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "Invalid JSON body or empty request"
        }), 400

    if 'title' in data:
        t = data['title']
        if not t or not isinstance(t, str) or not t.strip():
            return jsonify({"status": "error", "message": "Title cannot be empty"}), 400
        ach.title = t.strip()[:200]

    if 'description' in data:
        desc = data['description']
        ach.description = desc.strip() if isinstance(desc, str) and desc.strip() else None

    if 'achievement_date' in data:
        parsed_d = parse_date_str(data['achievement_date'])
        if not parsed_d:
            return jsonify({"status": "error", "message": "Invalid achievement_date format. Expected 'YYYY-MM-DD'"}), 400
        ach.achievement_date = parsed_d

    if 'achievement_url' in data:
        u = data['achievement_url']
        ach.achievement_url = u.strip()[:500] if isinstance(u, str) and u.strip() else None

    try:
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Achievement updated successfully",
            "achievement": format_achievement(ach)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to update achievement: {str(e)}"
        }), 500


@achievements_bp.route('/<int:achievement_id>', methods=['DELETE'])
@mentee_required
def delete_achievement(achievement_id: int):
    """
    Deletes an achievement.
    Restricted to the owner mentee.
    """
    user_id = int(get_jwt_identity())
    mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not mentee_prof:
        return jsonify({"status": "error", "message": "Mentee profile not found"}), 404

    ach = Achievement.query.get(achievement_id)
    if not ach:
        return jsonify({"status": "error", "message": f"Achievement {achievement_id} not found"}), 404

    if ach.mentee_id != mentee_prof.id:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you can only delete your own achievements"
        }), 403

    try:
        db.session.delete(ach)
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Achievement deleted successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to delete achievement: {str(e)}"
        }), 500
