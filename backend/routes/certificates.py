"""
Certificates management API endpoints.
Supports document uploading (PDF, PNG, JPG, JPEG), certificate metadata tracking,
mentee ownership isolation, and authenticated certificate downloading.
"""

import os
import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from extensions import db
from models import Certificate, MenteeProfile, User
from utils.auth import mentee_required

certificates_bp = Blueprint('certificates', __name__)

ALLOWED_EXTENSIONS = {
    'pdf': {'mime': 'application/pdf', 'type': 'pdf'},
    'jpg': {'mime': 'image/jpeg', 'type': 'jpg'},
    'jpeg': {'mime': 'image/jpeg', 'type': 'jpeg'},
    'png': {'mime': 'image/png', 'type': 'png'},
}

MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB


def get_upload_folder() -> str:
    """
    Returns absolute path to the backend uploads/certificates directory.
    Ensures directory exists.
    """
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir = os.path.join(backend_dir, 'uploads', 'certificates')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


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


def format_certificate(cert: Certificate) -> dict:
    """
    Formats a Certificate model instance into a JSON dictionary.
    """
    filename = os.path.basename(cert.file_path) if cert.file_path else None
    display_name = filename
    if filename and '_' in filename:
        parts = filename.split('_', 1)
        if len(parts[0]) == 32:
            display_name = parts[1]

    return {
        "id": cert.id,
        "mentee_id": cert.mentee_id,
        "title": cert.title,
        "issuer": cert.issuer,
        "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
        "file_path": cert.file_path or "",
        "file_name": display_name or filename or "",
        "file_type": cert.file_type or "",
        "created_at": cert.created_at.isoformat() if cert.created_at else None,
    }


@certificates_bp.route('', methods=['GET'])
@certificates_bp.route('/', methods=['GET'])
@mentee_required
def get_certificates():
    """
    Retrieves all certificates uploaded by the authenticated mentee.
    """
    user_id = int(get_jwt_identity())
    mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not mentee_prof:
        return jsonify({"status": "success", "count": 0, "certificates": []}), 200

    certs = Certificate.query.filter_by(
        mentee_id=mentee_prof.id
    ).order_by(Certificate.issue_date.desc(), Certificate.created_at.desc()).all()

    certs_data = [format_certificate(c) for c in certs]
    return jsonify({
        "status": "success",
        "count": len(certs_data),
        "certificates": certs_data
    }), 200


@certificates_bp.route('', methods=['POST'])
@certificates_bp.route('/', methods=['POST'])
@mentee_required
def upload_certificate():
    """
    Uploads a certificate document/image and stores metadata for the mentee.
    Accepts multipart/form-data.
    """
    user_id = int(get_jwt_identity())
    mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not mentee_prof:
        mentee_prof = MenteeProfile(user_id=user_id)
        db.session.add(mentee_prof)
        db.session.commit()

    title = request.form.get('title')
    issuer = request.form.get('issuer')
    issue_date_raw = request.form.get('issue_date')

    if not title or not title.strip():
        return jsonify({"status": "error", "message": "Certificate title is required"}), 400
    if not issuer or not issuer.strip():
        return jsonify({"status": "error", "message": "Certificate issuer is required"}), 400
    if not issue_date_raw or not issue_date_raw.strip():
        return jsonify({"status": "error", "message": "Issue date is required"}), 400

    issue_date = parse_date_str(issue_date_raw)
    if not issue_date:
        return jsonify({
            "status": "error",
            "message": "Invalid issue_date format. Expected 'YYYY-MM-DD'"
        }), 400

    if 'file' not in request.files:
        return jsonify({
            "status": "error",
            "message": "No certificate file uploaded. Please select a document (PDF, JPG, PNG)."
        }), 400

    file = request.files['file']
    if not file or not file.filename or not file.filename.strip():
        return jsonify({"status": "error", "message": "No file selected"}), 400

    clean_filename = secure_filename(file.filename)
    if not clean_filename or '.' not in clean_filename:
        return jsonify({"status": "error", "message": "Invalid filename"}), 400

    ext = clean_filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({
            "status": "error",
            "message": f"Unsupported file type '.{ext}'. Allowed types: PDF (.pdf), JPG (.jpg, .jpeg), PNG (.png)"
        }), 400

    # Validate file size
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    file.seek(0)

    if file_length == 0:
        return jsonify({"status": "error", "message": "Uploaded file is empty"}), 400

    if file_length > MAX_FILE_SIZE:
        return jsonify({
            "status": "error",
            "message": f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE // (1024 * 1024)}MB"
        }), 400

    # Generate unique filename and destination path
    unique_filename = f"{uuid.uuid4().hex}_{clean_filename}"
    upload_folder = get_upload_folder()
    dest_path = os.path.join(upload_folder, unique_filename)

    try:
        file.save(dest_path)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to save certificate file: {str(e)}"
        }), 500

    relative_file_path = f"uploads/certificates/{unique_filename}"
    file_type = ALLOWED_EXTENSIONS[ext]['type']

    try:
        new_cert = Certificate(
            mentee_id=mentee_prof.id,
            title=title.strip()[:200],
            issuer=issuer.strip()[:200],
            issue_date=issue_date,
            file_path=relative_file_path,
            file_type=file_type,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(new_cert)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Certificate uploaded successfully",
            "certificate": format_certificate(new_cert)
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
            "message": f"Failed to create certificate record: {str(e)}"
        }), 500


@certificates_bp.route('/<int:cert_id>', methods=['PUT'])
@mentee_required
def update_certificate(cert_id: int):
    """
    Updates certificate metadata (title, issuer, issue_date).
    Restricted to the owner mentee.
    """
    user_id = int(get_jwt_identity())
    mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not mentee_prof:
        return jsonify({"status": "error", "message": "Mentee profile not found"}), 404

    cert = Certificate.query.get(cert_id)
    if not cert:
        return jsonify({"status": "error", "message": f"Certificate {cert_id} not found"}), 404

    if cert.mentee_id != mentee_prof.id:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you can only update your own certificates"
        }), 403

    # Accepts both JSON or Form-data
    data = request.get_json(silent=True) or request.form

    if 'title' in data:
        t = data['title']
        if not t or not t.strip():
            return jsonify({"status": "error", "message": "Title cannot be empty"}), 400
        cert.title = t.strip()[:200]

    if 'issuer' in data:
        i = data['issuer']
        if not i or not i.strip():
            return jsonify({"status": "error", "message": "Issuer cannot be empty"}), 400
        cert.issuer = i.strip()[:200]

    if 'issue_date' in data:
        parsed_d = parse_date_str(data['issue_date'])
        if not parsed_d:
            return jsonify({"status": "error", "message": "Invalid issue_date format. Expected 'YYYY-MM-DD'"}), 400
        cert.issue_date = parsed_d

    try:
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Certificate updated successfully",
            "certificate": format_certificate(cert)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to update certificate: {str(e)}"
        }), 500


@certificates_bp.route('/<int:cert_id>/download', methods=['GET'])
@jwt_required()
def download_certificate(cert_id: int):
    """
    Authenticated endpoint to download / view certificate document.
    Restricted to the owning mentee.
    """
    user_id = int(get_jwt_identity())
    mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()

    cert = Certificate.query.get(cert_id)
    if not cert:
        return jsonify({"status": "error", "message": f"Certificate {cert_id} not found"}), 404

    if not mentee_prof or cert.mentee_id != mentee_prof.id:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you can only access your own certificates"
        }), 403

    if not cert.file_path:
        return jsonify({"status": "error", "message": "Certificate has no associated file"}), 404

    filename = os.path.basename(cert.file_path)
    upload_folder = get_upload_folder()
    abs_path = os.path.join(upload_folder, filename)

    if not os.path.exists(abs_path):
        return jsonify({"status": "error", "message": "Certificate file not found on server"}), 404

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


@certificates_bp.route('/<int:cert_id>', methods=['DELETE'])
@mentee_required
def delete_certificate(cert_id: int):
    """
    Deletes a certificate and removes its physical file from disk.
    Restricted to the owner mentee.
    """
    user_id = int(get_jwt_identity())
    mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not mentee_prof:
        return jsonify({"status": "error", "message": "Mentee profile not found"}), 404

    cert = Certificate.query.get(cert_id)
    if not cert:
        return jsonify({"status": "error", "message": f"Certificate {cert_id} not found"}), 404

    if cert.mentee_id != mentee_prof.id:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you can only delete your own certificates"
        }), 403

    if cert.file_path:
        filename = os.path.basename(cert.file_path)
        abs_path = os.path.join(get_upload_folder(), filename)
        if os.path.exists(abs_path):
            try:
                os.remove(abs_path)
            except OSError:
                pass

    try:
        db.session.delete(cert)
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "Certificate deleted successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"Failed to delete certificate: {str(e)}"
        }), 500
