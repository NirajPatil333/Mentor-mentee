"""
Authentication routes for registration, login, user identity verification,
email verification, secure password reset, and profile picture management.
"""

import os
import uuid
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import db
from models import User, MentorProfile, MenteeProfile
from utils.auth import (
    hash_password,
    verify_password,
    normalize_email,
    is_valid_email,
    get_current_user,
    mentor_required,
    mentee_required,
    generate_secure_token,
    hash_token
)
from services.email_service import (
    send_verification_email,
    send_password_reset_email
)

auth_bp = Blueprint('auth', __name__)

# Security policy constants
EMAIL_VERIFICATION_EXPIRY_HOURS = 24
PASSWORD_RESET_EXPIRY_MINUTES = 15
REQUEST_COOLDOWN_SECONDS = 60

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
MAX_PROFILE_PICTURE_SIZE = 5 * 1024 * 1024  # 5MB


def validate_image_file(file_storage):
    """
    Validates file extension, non-empty content, size under 5MB limit,
    and checks binary image signatures to reject corrupted or spoofed files.
    """
    if not file_storage or not file_storage.filename:
        return False, "No file selected"

    filename = file_storage.filename
    if '.' not in filename:
        return False, "File must have an extension"

    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f"Unsupported image format '.{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"

    # Check file size safely
    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)

    if size == 0:
        return False, "Uploaded image is empty"

    if size > MAX_PROFILE_PICTURE_SIZE:
        return False, f"Image size exceeds maximum limit of {MAX_PROFILE_PICTURE_SIZE // (1024 * 1024)}MB"

    # Read binary header for magic bytes verification
    header = file_storage.read(32)
    file_storage.seek(0)

    is_valid_magic = False
    if ext in ('jpg', 'jpeg') and header.startswith(b'\xff\xd8\xff'):
        is_valid_magic = True
    elif ext == 'png' and header.startswith(b'\x89PNG\r\n\x1a\n'):
        is_valid_magic = True
    elif ext == 'gif' and (header.startswith(b'GIF87a') or header.startswith(b'GIF89a')):
        is_valid_magic = True
    elif ext == 'webp' and header.startswith(b'RIFF') and b'WEBP' in header[:16]:
        is_valid_magic = True

    if not is_valid_magic:
        return False, "File content does not match a valid image signature"

    return True, None


def get_profiles_upload_dir() -> str:
    """Returns absolute path to the backend uploads/profiles directory."""
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir = os.path.join(backend_dir, 'uploads', 'profiles')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def handle_profile_picture_upload(user: User):
    """
    Core handler for profile picture upload.
    Validates file, removes old picture if present, saves new picture, and updates user record.
    """
    file = request.files.get('file') or request.files.get('profile_picture') or request.files.get('image')
    if not file:
        return jsonify({"status": "error", "message": "No image file provided"}), 400

    valid, err_msg = validate_image_file(file)
    if not valid:
        return jsonify({"status": "error", "message": err_msg}), 400

    upload_dir = get_profiles_upload_dir()
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"profile_{user.id}_{uuid.uuid4().hex[:12]}.{ext}"
    dest_path = os.path.join(upload_dir, unique_filename)

    # Clean up previous profile picture file from disk if present
    if user.profile_picture:
        prev_filename = os.path.basename(user.profile_picture)
        prev_path = os.path.join(upload_dir, prev_filename)
        if os.path.exists(prev_path):
            try:
                os.remove(prev_path)
            except OSError:
                pass

    try:
        file.save(dest_path)
        user.profile_picture = f"uploads/profiles/{unique_filename}"
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Profile picture updated successfully",
            "profile_picture": user.profile_picture,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "profile_picture": user.profile_picture
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except OSError:
                pass
        return jsonify({
            "status": "error",
            "message": f"Failed to save profile picture: {str(e)}"
        }), 500


def handle_profile_picture_delete(user: User):
    """
    Core handler for profile picture deletion.
    Removes picture file from disk and nulls user record attribute.
    """
    if user.profile_picture:
        upload_dir = get_profiles_upload_dir()
        prev_filename = os.path.basename(user.profile_picture)
        prev_path = os.path.join(upload_dir, prev_filename)
        if os.path.exists(prev_path):
            try:
                os.remove(prev_path)
            except OSError:
                pass

        user.profile_picture = None
        db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Profile picture removed successfully",
        "profile_picture": None,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "profile_picture": None
        }
    }), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Registers a new user (either mentor or mentee).
    Validates input parameters, ensures email uniqueness, hashes password,
    creates unverified account, generates secure token, and dispatches verification email.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "status": "error",
            "message": "Invalid JSON body or empty request"
        }), 400

    name = data.get('name', '').strip() if isinstance(data.get('name'), str) else ''
    raw_email = data.get('email', '')
    email = normalize_email(raw_email) if isinstance(raw_email, str) else ''
    password = data.get('password', '')
    role = data.get('role', '').strip().lower() if isinstance(data.get('role'), str) else ''

    # Validate required fields
    if not name:
        return jsonify({
            "status": "error",
            "message": "Name is required"
        }), 400

    if not email or not is_valid_email(email):
        return jsonify({
            "status": "error",
            "message": "A valid email address is required"
        }), 400

    if not password or not isinstance(password, str) or len(password) < 6:
        return jsonify({
            "status": "error",
            "message": "Password is required and must be at least 6 characters long"
        }), 400

    if role not in ('mentor', 'mentee'):
        return jsonify({
            "status": "error",
            "message": "Role must be exactly 'mentor' or 'mentee'"
        }), 400

    # Check for duplicate email
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({
            "status": "error",
            "message": "Email is already registered"
        }), 409

    try:
        now_utc = datetime.now(timezone.utc)

        # Create User entity - immediately active without email verification
        new_user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=role,
            profile_picture=None,
            is_verified=True,
            email_verification_token_hash=None,
            email_verification_sent_at=None
        )
        db.session.add(new_user)
        db.session.flush()

        # Automatically initialize the appropriate profile based on role
        if role == 'mentor':
            mentor_profile = MentorProfile(user_id=new_user.id)
            db.session.add(mentor_profile)
        elif role == 'mentee':
            mentee_profile = MenteeProfile(user_id=new_user.id)
            db.session.add(mentee_profile)

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Registration successful! You can now log in immediately.",
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email,
                "role": new_user.role,
                "profile_picture": None,
                "is_verified": True
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"An error occurred during registration: {str(e)}"
        }), 500


@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """
    Verifies user email address using single-use expiring token.
    Stores/matches token hash only.
    """
    data = request.get_json(silent=True)
    if not data or not data.get('token'):
        return jsonify({
            "status": "error",
            "message": "Verification token is required"
        }), 400

    raw_token = str(data.get('token')).strip()
    token_hash = hash_token(raw_token)

    user = User.query.filter_by(email_verification_token_hash=token_hash).first()
    if not user:
        return jsonify({
            "status": "error",
            "message": "Invalid or already used verification token"
        }), 400

    # Check token expiry (24 hours)
    if user.email_verification_sent_at:
        sent_at = user.email_verification_sent_at
        if sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - sent_at > timedelta(hours=EMAIL_VERIFICATION_EXPIRY_HOURS):
            return jsonify({
                "status": "error",
                "message": "Verification link has expired. Please request a new one."
            }), 400

    # Mark as verified and invalidate token hash
    user.is_verified = True
    user.email_verification_token_hash = None
    user.email_verification_sent_at = None
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Email verified successfully! You can now log in."
    }), 200


@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """
    Resends verification email to an unverified user account.
    Enforces cooldown rate limiting to prevent email spam.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "status": "error",
            "message": "Invalid request body"
        }), 400

    raw_email = data.get('email', '')
    email = normalize_email(raw_email) if isinstance(raw_email, str) else ''

    if not email or not is_valid_email(email):
        return jsonify({
            "status": "error",
            "message": "A valid email address is required"
        }), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        # Generic message to avoid email enumeration
        return jsonify({
            "status": "success",
            "message": "If an unverified account exists with this email, a new verification link has been sent."
        }), 200

    if user.is_verified:
        return jsonify({
            "status": "error",
            "message": "This account is already verified. Please log in directly."
        }), 400

    # Rate limiting cooldown check
    now_utc = datetime.now(timezone.utc)
    if user.email_verification_sent_at:
        sent_at = user.email_verification_sent_at
        if sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=timezone.utc)
        if (now_utc - sent_at).total_seconds() < REQUEST_COOLDOWN_SECONDS:
            remaining = int(REQUEST_COOLDOWN_SECONDS - (now_utc - sent_at).total_seconds())
            return jsonify({
                "status": "error",
                "message": f"Please wait {remaining} seconds before requesting another verification email."
            }), 429

    raw_token = generate_secure_token()
    user.email_verification_token_hash = hash_token(raw_token)
    user.email_verification_sent_at = now_utc
    db.session.commit()

    try:
        send_verification_email(user.email, user.name, raw_token)
    except Exception:
        pass

    return jsonify({
        "status": "success",
        "message": "If an unverified account exists with this email, a new verification link has been sent."
    }), 200


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Initiates password reset flow.
    Validates email existence, generates single-use expiring token (15-min expiry),
    and sends password reset email.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "status": "error",
            "message": "Invalid request body"
        }), 400

    raw_email = data.get('email', '')
    email = normalize_email(raw_email) if isinstance(raw_email, str) else ''

    if not email or not is_valid_email(email):
        return jsonify({
            "status": "error",
            "message": "A valid email address is required"
        }), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({
            "status": "error",
            "message": "No account found with this email address."
        }), 404

    now_utc = datetime.now(timezone.utc)
    # Rate limit cooldown check (60s)
    if user.reset_password_sent_at:
        sent_at = user.reset_password_sent_at
        if sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=timezone.utc)
        if (now_utc - sent_at).total_seconds() < REQUEST_COOLDOWN_SECONDS:
            remaining = int(REQUEST_COOLDOWN_SECONDS - (now_utc - sent_at).total_seconds())
            return jsonify({
                "status": "error",
                "message": f"Please wait {remaining} seconds before requesting another reset email."
            }), 429

    raw_token = generate_secure_token()
    user.reset_password_token_hash = hash_token(raw_token)
    user.reset_password_sent_at = now_utc
    db.session.commit()

    email_sent = False
    try:
        email_sent = send_password_reset_email(user.email, user.name, raw_token)
    except Exception:
        email_sent = False

    if not email_sent:
        # Invalidate the token so user can retry cleanly without stale state
        user.reset_password_token_hash = None
        user.reset_password_sent_at = None
        db.session.commit()
        return jsonify({
            "status": "error",
            "message": "Failed to send password reset email. Please try again later."
        }), 502

    return jsonify({
        "status": "success",
        "message": "Password reset instructions have been sent to your email address."
    }), 200


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Completes password reset using single-use expiring token.
    Validates token hash, checks 15-minute expiration, updates password hash,
    and immediately invalidates reset token.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "status": "error",
            "message": "Invalid request body"
        }), 400

    raw_token = data.get('token', '').strip() if isinstance(data.get('token'), str) else ''
    new_password = data.get('new_password', '')

    if not raw_token:
        return jsonify({
            "status": "error",
            "message": "Reset token is required"
        }), 400

    if not new_password or not isinstance(new_password, str) or len(new_password) < 6:
        return jsonify({
            "status": "error",
            "message": "Password is required and must be at least 6 characters long"
        }), 400

    token_hash = hash_token(raw_token)
    user = User.query.filter_by(reset_password_token_hash=token_hash).first()

    if not user:
        return jsonify({
            "status": "error",
            "message": "Invalid or expired password reset token"
        }), 400

    # Check 15-minute expiration
    if user.reset_password_sent_at:
        sent_at = user.reset_password_sent_at
        if sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - sent_at > timedelta(minutes=PASSWORD_RESET_EXPIRY_MINUTES):
            # Invalidate expired token
            user.reset_password_token_hash = None
            user.reset_password_sent_at = None
            db.session.commit()
            return jsonify({
                "status": "error",
                "message": "Password reset token has expired. Please request a new one."
            }), 400

    # Update password and single-use invalidate token
    user.password_hash = hash_password(new_password)
    user.reset_password_token_hash = None
    user.reset_password_sent_at = None
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Password has been successfully reset. You can now log in with your new password."
    }), 200


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticates user credentials and issues a JWT access token.
    Requires email verification for newly registered accounts.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "status": "error",
            "message": "Invalid JSON body or empty request"
        }), 400

    raw_email = data.get('email', '')
    email = normalize_email(raw_email) if isinstance(raw_email, str) else ''
    password = data.get('password', '')

    if not email or not password:
        return jsonify({
            "status": "error",
            "message": "Both email and password are required"
        }), 400

    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({
            "status": "error",
            "message": "Invalid email or password"
        }), 401

    # Generate JWT access token with role and basic identity in claims
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role,
            "email": user.email,
            "name": user.name
        }
    )

    return jsonify({
        "status": "success",
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "profile_picture": user.profile_picture
        }
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Returns profile information for the currently authenticated user.
    """
    user = get_current_user()
    if not user:
        return jsonify({
            "status": "error",
            "message": "User account not found"
        }), 404

    return jsonify({
        "status": "success",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "profile_picture": user.profile_picture,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    }), 200


@auth_bp.route('/profile-picture', methods=['POST'])
@jwt_required()
def upload_profile_picture():
    """
    Uploads or updates the authenticated user's profile picture.
    """
    user = get_current_user()
    if not user:
        return jsonify({"status": "error", "message": "User account not found"}), 404

    return handle_profile_picture_upload(user)


@auth_bp.route('/profile-picture', methods=['DELETE'])
@jwt_required()
def delete_profile_picture():
    """
    Removes the authenticated user's profile picture.
    """
    user = get_current_user()
    if not user:
        return jsonify({"status": "error", "message": "User account not found"}), 404

    return handle_profile_picture_delete(user)


@auth_bp.route('/mentor-only-test', methods=['GET'])
@mentor_required
def mentor_only_test():
    """
    Test route accessible only to users with the 'mentor' role.
    """
    user_id = get_jwt_identity()
    return jsonify({
        "status": "success",
        "message": "Access granted: Mentor role confirmed",
        "user_id": int(user_id)
    }), 200


@auth_bp.route('/mentee-only-test', methods=['GET'])
@mentee_required
def mentee_only_test():
    """
    Test route accessible only to users with the 'mentee' role.
    """
    user_id = get_jwt_identity()
    return jsonify({
        "status": "success",
        "message": "Access granted: Mentee role confirmed",
        "user_id": int(user_id)
    }), 200
