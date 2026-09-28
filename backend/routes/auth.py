"""
Authentication routes for registration, login, and user identity verification.
"""

from flask import Blueprint, request, jsonify
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
    mentee_required
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Registers a new user (either mentor or mentee).
    Validates input parameters, ensures email uniqueness, hashes password,
    and initializes corresponding profile row.
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
        # Create User entity
        new_user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=role
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
            "message": "User registered successfully",
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email,
                "role": new_user.role
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"An error occurred during registration: {str(e)}"
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticates user credentials and issues a JWT access token.
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
            "role": user.role
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
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    }), 200


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
