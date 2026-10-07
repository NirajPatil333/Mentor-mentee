"""
Resource management API endpoints.
Supports document uploading (PDF, Word, PPT), retrieval with mentorship-scoped authorization,
and authenticated document downloading.
"""

import os
import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from extensions import db
from models import Resource, MentorProfile, MenteeProfile, MentorshipRequest, User
from utils.auth import mentor_required

resources_bp = Blueprint('resources', __name__)

ALLOWED_EXTENSIONS = {
    'pdf': {'mime': 'application/pdf', 'type': 'pdf'},
    'ppt': {'mime': 'application/vnd.ms-powerpoint', 'type': 'powerpoint'},
    'pptx': {'mime': 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'type': 'powerpoint'},
    'doc': {'mime': 'application/msword', 'type': 'word'},
    'docx': {'mime': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'type': 'word'}
}

MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB


def get_upload_folder() -> str:
    """
    Returns absolute path to the backend uploads/resources directory.
    Creates directory if it doesn't already exist.
    """
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir = os.path.join(backend_dir, 'uploads', 'resources')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def format_resource(res: Resource) -> dict:
    """
    Formats a Resource model instance into a JSON-serializable dictionary
    including mentor and mentee metadata, file names, and timestamps.
    """
    mentor_prof = res.mentor
    mentor_user = mentor_prof.user if mentor_prof else None
    mentee_prof = res.mentee
    mentee_user = mentee_prof.user if mentee_prof else None

    filename = os.path.basename(res.file_path) if res.file_path else None
    display_name = filename
    if filename and '_' in filename:
        parts = filename.split('_', 1)
        if len(parts[0]) == 32:
            display_name = parts[1]

    return {
        "id": res.id,
        "mentor_id": res.mentor_id,
        "mentee_id": res.mentee_id,
        "title": res.title,
        "description": res.description or "",
        "resource_type": res.resource_type,
        "resource_url": res.resource_url or "",
        "file_path": res.file_path or "",
        "file_name": display_name or filename or "",
        "created_at": res.created_at.isoformat() if res.created_at else None,
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


@resources_bp.route('', methods=['GET'])
@resources_bp.route('/', methods=['GET'])
@jwt_required()
def get_resources():
    """
    Retrieves resources visible to the authenticated user.
    - Mentors see all resources they have uploaded.
    - Mentees see resources shared by mentors with whom they have an accepted mentorship,
      either shared generally (mentee_id is None) or specifically with them.
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    if user.role == 'mentor':
        mentor_prof = MentorProfile.query.filter_by(user_id=user_id).first()
        if not mentor_prof:
            return jsonify({"status": "success", "count": 0, "resources": []}), 200

        resources = Resource.query.filter_by(
            mentor_id=mentor_prof.id
        ).order_by(Resource.created_at.desc()).all()

    elif user.role == 'mentee':
        mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()
        if not mentee_prof:
            return jsonify({"status": "success", "count": 0, "resources": []}), 200

        accepted_requests = MentorshipRequest.query.filter_by(
            mentee_id=mentee_prof.id,
            status='accepted'
        ).all()
        mentor_ids = [req.mentor_id for req in accepted_requests]

        if not mentor_ids:
            return jsonify({"status": "success", "count": 0, "resources": []}), 200

        resources = Resource.query.filter(
            Resource.mentor_id.in_(mentor_ids),
            db.or_(Resource.mentee_id == mentee_prof.id, Resource.mentee_id.is_(None))
        ).order_by(Resource.created_at.desc()).all()

    else:
        return jsonify({"status": "error", "message": "Invalid user role"}), 403

    resources_data = [format_resource(r) for r in resources]
    return jsonify({
        "status": "success",
        "count": len(resources_data),
        "resources": resources_data
    }), 200


@resources_bp.route('/my-mentees', methods=['GET'])
@mentor_required
def get_mentor_mentees():
    """
    Retrieves the list of accepted mentees for the authenticated mentor.
    Useful for populating mentee target dropdowns in the upload interface.
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


@resources_bp.route('', methods=['POST'])
@resources_bp.route('/', methods=['POST'])
@mentor_required
def upload_resource():
    """
    Uploads a new document resource (PDF, Word, PPT).
    Only authenticated mentors can upload resources.
    Validates file extension, size, and mentor-mentee relationship if mentee_id is provided.
    """
    user_id = int(get_jwt_identity())
    mentor_prof = MentorProfile.query.filter_by(user_id=user_id).first()
    if not mentor_prof:
        mentor_prof = MentorProfile(user_id=user_id)
        db.session.add(mentor_prof)
        db.session.commit()

    title = request.form.get('title')
    if not title or not title.strip():
        return jsonify({"status": "error", "message": "Title is required"}), 400

    description = request.form.get('description', '')
    mentee_id_raw = request.form.get('mentee_id')

    if 'file' not in request.files:
        return jsonify({
            "status": "error",
            "message": "No file uploaded. Please select a document (PDF, Word, or PowerPoint)."
        }), 400

    file = request.files['file']
    if not file or not file.filename or not file.filename.strip():
        return jsonify({
            "status": "error",
            "message": "No file selected"
        }), 400

    raw_filename = file.filename
    clean_filename = secure_filename(raw_filename)
    if not clean_filename or '.' not in clean_filename:
        return jsonify({
            "status": "error",
            "message": "Invalid filename format"
        }), 400

    ext = clean_filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({
            "status": "error",
            "message": f"Unsupported file type '.{ext}'. Allowed types: PDF (.pdf), Word (.doc, .docx), PowerPoint (.ppt, .pptx)"
        }), 400

    # Validate file size
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    file.seek(0)

    if file_length == 0:
        return jsonify({
            "status": "error",
            "message": "Uploaded file is empty"
        }), 400

    if file_length > MAX_FILE_SIZE:
        return jsonify({
            "status": "error",
            "message": f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE // (1024 * 1024)}MB"
        }), 400

    target_mentee_id = None
    if mentee_id_raw and str(mentee_id_raw).strip().lower() not in ('', 'null', 'none', 'all', '0'):
        try:
            m_id = int(mentee_id_raw)
            mentee_prof = MenteeProfile.query.get(m_id)
            if not mentee_prof:
                mentee_prof = MenteeProfile.query.filter_by(user_id=m_id).first()

            if not mentee_prof:
                return jsonify({
                    "status": "error",
                    "message": f"Mentee profile with ID {m_id} not found"
                }), 404

            # Validate accepted mentorship relationship
            rel = MentorshipRequest.query.filter_by(
                mentor_id=mentor_prof.id,
                mentee_id=mentee_prof.id,
                status='accepted'
            ).first()

            if not rel:
                return jsonify({
                    "status": "error",
                    "message": "Targeted resources can only be shared with mentees who have an accepted mentorship request with you"
                }), 403

            target_mentee_id = mentee_prof.id
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Invalid mentee_id format"}), 400

    # Generate safe unique filename
    unique_filename = f"{uuid.uuid4().hex}_{clean_filename}"
    upload_folder = get_upload_folder()
    dest_path = os.path.join(upload_folder, unique_filename)

    try:
        file.save(dest_path)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to save uploaded file: {str(e)}"
        }), 500

    relative_file_path = f"uploads/resources/{unique_filename}"
    resource_type = ALLOWED_EXTENSIONS[ext]['type']

    try:
        new_resource = Resource(
            mentor_id=mentor_prof.id,
            mentee_id=target_mentee_id,
            title=title.strip()[:200],
            description=description.strip() if isinstance(description, str) and description.strip() else None,
            resource_type=resource_type,
            resource_url=None,
            file_path=relative_file_path,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(new_resource)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Resource uploaded successfully",
            "resource": format_resource(new_resource)
        }), 201

    except Exception as e:
        db.session.rollback()
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except OSError:
                pass
        return jsonify({
            "status": "error",
            "message": f"Failed to record resource in database: {str(e)}"
        }), 500


@resources_bp.route('/<int:resource_id>/download', methods=['GET'])
@jwt_required()
def download_resource(resource_id: int):
    """
    Authenticated endpoint to download or open a resource file.
    Validates that the requesting user is the owning mentor or an authorized mentee.
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    resource = Resource.query.get(resource_id)
    if not resource:
        return jsonify({"status": "error", "message": f"Resource {resource_id} not found"}), 404

    is_authorized = False

    if user.role == 'mentor':
        mentor_prof = MentorProfile.query.filter_by(user_id=user_id).first()
        if mentor_prof and resource.mentor_id == mentor_prof.id:
            is_authorized = True
    elif user.role == 'mentee':
        mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()
        if mentee_prof:
            # Check accepted mentorship relationship with the resource's mentor
            rel = MentorshipRequest.query.filter_by(
                mentor_id=resource.mentor_id,
                mentee_id=mentee_prof.id,
                status='accepted'
            ).first()

            if rel and (resource.mentee_id == mentee_prof.id or resource.mentee_id is None):
                is_authorized = True

    if not is_authorized:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you are not authorized to download this resource"
        }), 403

    if not resource.file_path:
        return jsonify({"status": "error", "message": "Resource has no associated file"}), 404

    filename = os.path.basename(resource.file_path)
    upload_folder = get_upload_folder()
    abs_path = os.path.join(upload_folder, filename)

    if not os.path.exists(abs_path):
        return jsonify({"status": "error", "message": "Document file not found on server"}), 404

    display_name = filename
    if '_' in filename:
        parts = filename.split('_', 1)
        if len(parts[0]) == 32:
            display_name = parts[1]

    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    mimetype = ALLOWED_EXTENSIONS.get(ext, {}).get('mime', 'application/octet-stream')

    return send_file(
        abs_path,
        mimetype=mimetype,
        as_attachment=True,
        download_name=display_name
    )


@resources_bp.route('/<int:resource_id>', methods=['DELETE'])
@mentor_required
def delete_resource(resource_id: int):
    """
    Allows the creator mentor to delete a resource and remove its file from disk.
    """
    user_id = int(get_jwt_identity())
    mentor_prof = MentorProfile.query.filter_by(user_id=user_id).first()
    if not mentor_prof:
        return jsonify({"status": "error", "message": "Mentor profile not found"}), 404

    resource = Resource.query.get(resource_id)
    if not resource:
        return jsonify({"status": "error", "message": f"Resource {resource_id} not found"}), 404

    if resource.mentor_id != mentor_prof.id:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you can only delete resources you uploaded"
        }), 403

    if resource.file_path:
        filename = os.path.basename(resource.file_path)
        abs_path = os.path.join(get_upload_folder(), filename)
        if os.path.exists(abs_path):
            try:
                os.remove(abs_path)
            except OSError:
                pass

    try:
        db.session.delete(resource)
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Resource deleted successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to delete resource: {str(e)}"
        }), 500
