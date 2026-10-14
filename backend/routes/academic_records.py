"""
Academic Records and Performance API endpoints.
Supports semester-wise SGPA tracking, automatic CGPA calculation (simple arithmetic average),
marksheet document uploading/previewing/downloading, and mentor verification workflow.
"""

import os
import uuid
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from extensions import db
from models import (
    AcademicRecord, MenteeProfile, MentorProfile, MentorshipRequest, User
)
from utils.auth import mentee_required, mentor_required

academic_records_bp = Blueprint('academic_records', __name__)

ALLOWED_EXTENSIONS = {
    'pdf': {'mime': 'application/pdf', 'type': 'pdf'},
    'jpg': {'mime': 'image/jpeg', 'type': 'jpg'},
    'jpeg': {'mime': 'image/jpeg', 'type': 'jpeg'},
    'png': {'mime': 'image/png', 'type': 'png'},
}

MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB


def get_upload_folder() -> str:
    """
    Returns absolute path to the backend uploads/marksheets directory.
    Ensures directory exists.
    """
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir = os.path.join(backend_dir, 'uploads', 'marksheets')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def calculate_cgpa(records) -> float:
    """
    Calculates arithmetic average CGPA from a list of AcademicRecord instances:
    CGPA = Sum of all entered semester SGPAs / Number of entered semesters.
    Returns rounded float to 2 decimal places. Returns 0.0 if no records.
    """
    valid_sgpas = [r.sgpa for r in records if r.sgpa is not None]
    if not valid_sgpas:
        return 0.0
    return round(sum(valid_sgpas) / len(valid_sgpas), 2)


def format_academic_record(rec: AcademicRecord) -> dict:
    """
    Formats an AcademicRecord model instance into a JSON-serializable dictionary.
    Includes reviewer metadata if available.
    """
    reviewer = rec.verified_by
    reviewer_user = reviewer.user if reviewer else None

    filename = os.path.basename(rec.file_path) if rec.file_path else None
    display_name = rec.file_name or filename
    if not display_name and filename and '_' in filename:
        parts = filename.split('_', 1)
        if len(parts[0]) == 32:
            display_name = parts[1]

    return {
        "id": rec.id,
        "mentee_id": rec.mentee_id,
        "semester": rec.semester,
        "semester_name": f"Semester {rec.semester}",
        "sgpa": round(float(rec.sgpa), 2) if rec.sgpa is not None else None,
        "file_path": rec.file_path or "",
        "file_name": display_name or "",
        "file_type": rec.file_type or "",
        "has_marksheet": bool(rec.file_path),
        "verification_status": rec.verification_status,
        "verified_by_mentor_id": rec.verified_by_mentor_id,
        "verified_by_name": reviewer_user.name if reviewer_user else None,
        "verified_at": rec.verified_at.isoformat() if rec.verified_at else None,
        "review_note": rec.review_note or "",
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
        "updated_at": rec.updated_at.isoformat() if rec.updated_at else None
    }


def can_user_access_academic_record(user_id: int, record: AcademicRecord) -> bool:
    """
    Checks if authenticated user is authorized to view or download marksheet files.
    Permits the owning mentee, or an accepted mentor of the mentee.
    """
    mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()
    if mentee_prof and record.mentee_id == mentee_prof.id:
        return True

    mentor_prof = MentorProfile.query.filter_by(user_id=user_id).first()
    if mentor_prof:
        active_req = MentorshipRequest.query.filter_by(
            mentor_id=mentor_prof.id,
            mentee_id=record.mentee_id,
            status='accepted'
        ).first()
        if active_req:
            return True

    return False


# =====================================================================
# MENTEE ENDPOINTS
# =====================================================================

@academic_records_bp.route('', methods=['GET'])
@academic_records_bp.route('/', methods=['GET'])
@mentee_required
def get_mentee_academic_records():
    """
    Retrieves all academic semester records for the authenticated mentee
    along with the automatically calculated CGPA (simple arithmetic average).
    """
    user_id = int(get_jwt_identity())
    mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not mentee_prof:
        return jsonify({
            "status": "success",
            "count": 0,
            "cgpa": 0.0,
            "cgpa_label": "Calculated CGPA (Simple Average)",
            "records": []
        }), 200

    records = AcademicRecord.query.filter_by(
        mentee_id=mentee_prof.id
    ).order_by(AcademicRecord.semester.asc()).all()

    cgpa = calculate_cgpa(records)
    records_data = [format_academic_record(r) for r in records]

    return jsonify({
        "status": "success",
        "count": len(records_data),
        "cgpa": cgpa,
        "cgpa_label": "Calculated CGPA (Simple Average)",
        "records": records_data
    }), 200


@academic_records_bp.route('', methods=['POST'])
@academic_records_bp.route('/', methods=['POST'])
@mentee_required
def create_academic_record():
    """
    Creates a new semester SGPA record for the authenticated mentee.
    Accepts JSON or multipart/form-data (with optional marksheet file).
    Enforces SGPA range [0.0, 10.0] and prevents duplicate semester records.
    """
    user_id = int(get_jwt_identity())
    mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not mentee_prof:
        mentee_prof = MenteeProfile(user_id=user_id)
        db.session.add(mentee_prof)
        db.session.commit()

    is_form = request.content_type and 'multipart/form-data' in request.content_type
    data = request.form if is_form else (request.get_json(silent=True) or {})

    semester_raw = data.get('semester')
    sgpa_raw = data.get('sgpa')

    # Validate semester
    if semester_raw is None or str(semester_raw).strip() == '':
        return jsonify({"status": "error", "message": "Semester number is required"}), 400

    try:
        semester_str = str(semester_raw).strip()
        if semester_str.lower().startswith('semester'):
            semester_str = semester_str.replace('semester', '').replace('Semester', '').strip()
        semester = int(semester_str)
        if semester < 1 or semester > 16:
            return jsonify({"status": "error", "message": "Semester must be a valid number between 1 and 16"}), 400
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Semester must be an integer"}), 400

    # Validate SGPA
    if sgpa_raw is None or str(sgpa_raw).strip() == '':
        return jsonify({"status": "error", "message": "SGPA is required"}), 400

    try:
        sgpa = float(sgpa_raw)
        if sgpa < 0.0 or sgpa > 10.0:
            return jsonify({
                "status": "error",
                "message": "SGPA must be between 0.0 and 10.0"
            }), 400
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "SGPA must be a valid decimal number"}), 400

    # Prevent duplicate semester record
    existing = AcademicRecord.query.filter_by(
        mentee_id=mentee_prof.id,
        semester=semester
    ).first()
    if existing:
        return jsonify({
            "status": "error",
            "message": f"A record for Semester {semester} already exists. Please edit the existing record."
        }), 409

    file_path = None
    file_name = None
    file_type = None

    # Handle optional marksheet file upload
    file = request.files.get('file') or request.files.get('marksheet')
    if file and file.filename and file.filename.strip():
        clean_name = secure_filename(file.filename)
        if not clean_name or '.' not in clean_name:
            return jsonify({"status": "error", "message": "Invalid file name"}), 400

        ext = clean_name.rsplit('.', 1)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({
                "status": "error",
                "message": f"Unsupported file type '.{ext}'. Allowed types: PDF, JPG, JPEG, PNG"
            }), 400

        # Validate file size
        file.seek(0, os.SEEK_END)
        file_len = file.tell()
        file.seek(0)

        if file_len == 0:
            return jsonify({"status": "error", "message": "Uploaded file is empty"}), 400
        if file_len > MAX_FILE_SIZE:
            return jsonify({
                "status": "error",
                "message": f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE // (1024 * 1024)}MB"
            }), 400

        unique_name = f"{uuid.uuid4().hex}_{clean_name}"
        upload_folder = get_upload_folder()
        dest = os.path.join(upload_folder, unique_name)

        try:
            file.save(dest)
            file_path = f"uploads/marksheets/{unique_name}"
            file_name = clean_name
            file_type = ALLOWED_EXTENSIONS[ext]['type']
        except Exception as e:
            return jsonify({"status": "error", "message": f"Failed to save marksheet: {str(e)}"}), 500

    try:
        new_record = AcademicRecord(
            mentee_id=mentee_prof.id,
            semester=semester,
            sgpa=round(sgpa, 2),
            file_path=file_path,
            file_name=file_name,
            file_type=file_type,
            verification_status='pending',
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.session.add(new_record)
        db.session.commit()

        # Recalculate CGPA
        all_records = AcademicRecord.query.filter_by(mentee_id=mentee_prof.id).all()
        cgpa = calculate_cgpa(all_records)

        return jsonify({
            "status": "success",
            "message": f"Academic record for Semester {semester} added successfully",
            "record": format_academic_record(new_record),
            "cgpa": cgpa,
            "cgpa_label": "Calculated CGPA (Simple Average)"
        }), 201

    except Exception as e:
        db.session.rollback()
        if file_path:
            abs_dest = os.path.join(get_upload_folder(), os.path.basename(file_path))
            if os.path.exists(abs_dest):
                try:
                    os.remove(abs_dest)
                except OSError:
                    pass
        return jsonify({"status": "error", "message": f"Failed to create academic record: {str(e)}"}), 500


@academic_records_bp.route('/<int:record_id>', methods=['PUT', 'PATCH'])
@mentee_required
def update_academic_record(record_id: int):
    """
    Updates an existing semester SGPA record.
    If SGPA is modified or a new marksheet is uploaded, resets verification to 'pending'.
    """
    user_id = int(get_jwt_identity())
    mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not mentee_prof:
        return jsonify({"status": "error", "message": "Mentee profile not found"}), 404

    record = AcademicRecord.query.get(record_id)
    if not record:
        return jsonify({"status": "error", "message": f"Academic record {record_id} not found"}), 404

    if record.mentee_id != mentee_prof.id:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you can only modify your own academic records"
        }), 403

    is_form = request.content_type and 'multipart/form-data' in request.content_type
    data = request.form if is_form else (request.get_json(silent=True) or {})

    # Update Semester if provided
    if 'semester' in data and data['semester'] is not None and str(data['semester']).strip() != '':
        try:
            s_str = str(data['semester']).strip()
            if s_str.lower().startswith('semester'):
                s_str = s_str.replace('semester', '').replace('Semester', '').strip()
            new_sem = int(s_str)
            if new_sem < 1 or new_sem > 16:
                return jsonify({"status": "error", "message": "Semester must be between 1 and 16"}), 400

            if new_sem != record.semester:
                duplicate = AcademicRecord.query.filter_by(
                    mentee_id=mentee_prof.id,
                    semester=new_sem
                ).first()
                if duplicate and duplicate.id != record.id:
                    return jsonify({
                        "status": "error",
                        "message": f"A record for Semester {new_sem} already exists."
                    }), 409
                record.semester = new_sem
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "Semester must be a valid integer"}), 400

    reset_to_pending = False

    # Update SGPA if provided
    if 'sgpa' in data and data['sgpa'] is not None and str(data['sgpa']).strip() != '':
        try:
            new_sgpa = float(data['sgpa'])
            if new_sgpa < 0.0 or new_sgpa > 10.0:
                return jsonify({"status": "error", "message": "SGPA must be between 0.0 and 10.0"}), 400
            if round(new_sgpa, 2) != record.sgpa:
                record.sgpa = round(new_sgpa, 2)
                reset_to_pending = True
        except (ValueError, TypeError):
            return jsonify({"status": "error", "message": "SGPA must be a valid decimal number"}), 400

    # Handle file replacement if uploaded
    file = request.files.get('file') or request.files.get('marksheet')
    old_file_to_delete = None
    if file and file.filename and file.filename.strip():
        clean_name = secure_filename(file.filename)
        if not clean_name or '.' not in clean_name:
            return jsonify({"status": "error", "message": "Invalid file name"}), 400

        ext = clean_name.rsplit('.', 1)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({
                "status": "error",
                "message": f"Unsupported file type '.{ext}'. Allowed types: PDF, JPG, JPEG, PNG"
            }), 400

        file.seek(0, os.SEEK_END)
        file_len = file.tell()
        file.seek(0)

        if file_len == 0:
            return jsonify({"status": "error", "message": "Uploaded file is empty"}), 400
        if file_len > MAX_FILE_SIZE:
            return jsonify({
                "status": "error",
                "message": f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE // (1024 * 1024)}MB"
            }), 400

        unique_name = f"{uuid.uuid4().hex}_{clean_name}"
        upload_folder = get_upload_folder()
        dest = os.path.join(upload_folder, unique_name)

        try:
            file.save(dest)
            old_file_to_delete = record.file_path
            record.file_path = f"uploads/marksheets/{unique_name}"
            record.file_name = clean_name
            record.file_type = ALLOWED_EXTENSIONS[ext]['type']
            reset_to_pending = True
        except Exception as e:
            return jsonify({"status": "error", "message": f"Failed to save marksheet: {str(e)}"}), 500

    # Reset verification status if SGPA changed or new marksheet uploaded
    if reset_to_pending:
        record.verification_status = 'pending'
        record.verified_by_mentor_id = None
        record.verified_at = None
        record.review_note = None

    record.updated_at = datetime.now(timezone.utc)

    try:
        db.session.commit()

        # Safely remove previous file if replaced
        if old_file_to_delete:
            old_abs = os.path.join(get_upload_folder(), os.path.basename(old_file_to_delete))
            if os.path.exists(old_abs):
                try:
                    os.remove(old_abs)
                except OSError:
                    pass

        all_records = AcademicRecord.query.filter_by(mentee_id=mentee_prof.id).all()
        cgpa = calculate_cgpa(all_records)

        return jsonify({
            "status": "success",
            "message": f"Academic record for Semester {record.semester} updated successfully",
            "record": format_academic_record(record),
            "cgpa": cgpa,
            "cgpa_label": "Calculated CGPA (Simple Average)"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Failed to update academic record: {str(e)}"}), 500


@academic_records_bp.route('/<int:record_id>', methods=['DELETE'])
@mentee_required
def delete_academic_record(record_id: int):
    """
    Deletes an academic record and any associated marksheet file on disk.
    Automatically recalculates CGPA.
    """
    user_id = int(get_jwt_identity())
    mentee_prof = MenteeProfile.query.filter_by(user_id=user_id).first()
    if not mentee_prof:
        return jsonify({"status": "error", "message": "Mentee profile not found"}), 404

    record = AcademicRecord.query.get(record_id)
    if not record:
        return jsonify({"status": "error", "message": f"Academic record {record_id} not found"}), 404

    if record.mentee_id != mentee_prof.id:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you can only delete your own academic records"
        }), 403

    file_to_remove = record.file_path

    try:
        db.session.delete(record)
        db.session.commit()

        if file_to_remove:
            abs_path = os.path.join(get_upload_folder(), os.path.basename(file_to_remove))
            if os.path.exists(abs_path):
                try:
                    os.remove(abs_path)
                except OSError:
                    pass

        all_records = AcademicRecord.query.filter_by(mentee_id=mentee_prof.id).all()
        cgpa = calculate_cgpa(all_records)

        return jsonify({
            "status": "success",
            "message": "Academic record deleted successfully",
            "cgpa": cgpa,
            "cgpa_label": "Calculated CGPA (Simple Average)",
            "remaining_count": len(all_records)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Failed to delete academic record: {str(e)}"}), 500


# =====================================================================
# SECURE PREVIEW & DOWNLOAD ENDPOINTS
# =====================================================================

@academic_records_bp.route('/<int:record_id>/preview', methods=['GET'])
@jwt_required()
def preview_marksheet(record_id: int):
    """
    Authenticated endpoint to preview marksheet document inline in browser.
    Restricted to authorized users (owner mentee or accepted mentor).
    """
    user_id = int(get_jwt_identity())
    record = AcademicRecord.query.get(record_id)
    if not record:
        return jsonify({"status": "error", "message": f"Academic record {record_id} not found"}), 404

    if not can_user_access_academic_record(user_id, record):
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you do not have permission to access this marksheet"
        }), 403

    if not record.file_path:
        return jsonify({"status": "error", "message": "No marksheet file uploaded for this semester"}), 404

    filename = os.path.basename(record.file_path)
    abs_path = os.path.join(get_upload_folder(), filename)

    if not os.path.exists(abs_path):
        return jsonify({"status": "error", "message": "Marksheet file not found on server"}), 404

    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    mimetype = ALLOWED_EXTENSIONS.get(ext, {}).get('mime', 'application/octet-stream')
    display_name = record.file_name or filename

    return send_file(
        abs_path,
        mimetype=mimetype,
        as_attachment=False,
        download_name=display_name
    )


@academic_records_bp.route('/<int:record_id>/download', methods=['GET'])
@jwt_required()
def download_marksheet(record_id: int):
    """
    Authenticated endpoint to download marksheet document as an attachment.
    Restricted to authorized users (owner mentee or accepted mentor).
    """
    user_id = int(get_jwt_identity())
    record = AcademicRecord.query.get(record_id)
    if not record:
        return jsonify({"status": "error", "message": f"Academic record {record_id} not found"}), 404

    if not can_user_access_academic_record(user_id, record):
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you do not have permission to access this marksheet"
        }), 403

    if not record.file_path:
        return jsonify({"status": "error", "message": "No marksheet file uploaded for this semester"}), 404

    filename = os.path.basename(record.file_path)
    abs_path = os.path.join(get_upload_folder(), filename)

    if not os.path.exists(abs_path):
        return jsonify({"status": "error", "message": "Marksheet file not found on server"}), 404

    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    mimetype = ALLOWED_EXTENSIONS.get(ext, {}).get('mime', 'application/octet-stream')
    display_name = record.file_name or filename

    return send_file(
        abs_path,
        mimetype=mimetype,
        as_attachment=True,
        download_name=display_name
    )


# =====================================================================
# MENTOR ENDPOINTS
# =====================================================================

@academic_records_bp.route('/mentee/<int:mentee_id>', methods=['GET'])
@mentor_required
def get_mentee_academic_records_by_mentor(mentee_id: int):
    """
    Retrieves all academic records and calculated CGPA for an accepted mentee.
    Restricted to mentors with an active accepted mentorship relationship.
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

    # Verify accepted mentorship relationship
    active_req = MentorshipRequest.query.filter_by(
        mentor_id=mentor_prof.id,
        mentee_id=mentee_prof.id,
        status='accepted'
    ).first()

    if not active_req:
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
            "email": mentee_user.email if mentee_user else ""
        },
        "count": len(records_data),
        "cgpa": cgpa,
        "cgpa_label": "Calculated CGPA (Simple Average)",
        "records": records_data
    }), 200


@academic_records_bp.route('/<int:record_id>/verify', methods=['PATCH'])
@mentor_required
def verify_academic_record(record_id: int):
    """
    Allows an authorized mentor to mark an academic record as 'verified' or 'rejected'.
    Stores the reviewing mentor's ID, verification timestamp, and review note.
    """
    user_id = int(get_jwt_identity())
    mentor_prof = MentorProfile.query.filter_by(user_id=user_id).first()
    if not mentor_prof:
        return jsonify({"status": "error", "message": "Mentor profile not found"}), 403

    record = AcademicRecord.query.get(record_id)
    if not record:
        return jsonify({"status": "error", "message": f"Academic record {record_id} not found"}), 404

    # Verify mentorship relationship
    active_req = MentorshipRequest.query.filter_by(
        mentor_id=mentor_prof.id,
        mentee_id=record.mentee_id,
        status='accepted'
    ).first()

    if not active_req:
        return jsonify({
            "status": "error",
            "message": "Access forbidden: you do not have an accepted mentorship with this mentee"
        }), 403

    data = request.get_json(silent=True) or {}
    status_raw = data.get('status')
    review_note = data.get('review_note')

    if not status_raw or not isinstance(status_raw, str):
        return jsonify({
            "status": "error",
            "message": "Verification status is required ('verified' or 'rejected')"
        }), 400

    status = status_raw.strip().lower()
    if status not in ('verified', 'rejected'):
        return jsonify({
            "status": "error",
            "message": "Invalid status. Allowed values: 'verified' or 'rejected'"
        }), 400

    clean_note = review_note.strip()[:1000] if isinstance(review_note, str) and review_note.strip() else None

    try:
        record.verification_status = status
        record.verified_by_mentor_id = mentor_prof.id
        record.verified_at = datetime.now(timezone.utc)
        record.review_note = clean_note
        record.updated_at = datetime.now(timezone.utc)

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": f"Academic record marked as {status.capitalize()}",
            "record": format_academic_record(record)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Failed to verify academic record: {str(e)}"}), 500
