"""
Authentication utilities, password hashing helpers, and role-based access decorators.
"""

import re
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models import User


def hash_password(password: str) -> str:
    """
    Hashes a plain-text password using Werkzeug's default PBKDF2/SHA256 algorithm.
    """
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Securely verifies a plain-text password against a stored password hash.
    """
    if not password or not password_hash:
        return False
    return check_password_hash(password_hash, password)


def normalize_email(email: str) -> str:
    """
    Trims whitespace and converts the email address to lowercase.
    """
    if not email:
        return ""
    return email.strip().lower()


def is_valid_email(email: str) -> bool:
    """
    Validates the structure of an email address using a standard regex.
    """
    if not email:
        return False
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(email_regex, email.strip()))


def get_current_user():
    """
    Retrieves the currently authenticated User instance from the JWT identity.
    Returns None if no user identity is found or the user does not exist in the database.
    """
    identity = get_jwt_identity()
    if not identity:
        return None
    try:
        user_id = int(identity)
        return User.query.get(user_id)
    except (ValueError, TypeError):
        return None


def role_required(*allowed_roles):
    """
    Decorator that verifies the JWT in the request and ensures the user's role
    matches one of the allowed roles.
    Returns HTTP 401 if token is invalid/missing, or HTTP 403 if role is unauthorized.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Verify JWT in the current request (raises appropriate 401 if missing/invalid)
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get('role')

            if user_role not in allowed_roles:
                return jsonify({
                    "status": "error",
                    "message": f"Access forbidden: requires one of the following roles: {', '.join(allowed_roles)}"
                }), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def mentor_required(fn):
    """
    Decorator that restricts access strictly to authenticated users with the 'mentor' role.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('role') != 'mentor':
            return jsonify({
                "status": "error",
                "message": "Access forbidden: mentor role required"
            }), 403
        return fn(*args, **kwargs)
    return wrapper


def mentee_required(fn):
    """
    Decorator that restricts access strictly to authenticated users with the 'mentee' role.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('role') != 'mentee':
            return jsonify({
                "status": "error",
                "message": "Access forbidden: mentee role required"
            }), 403
        return fn(*args, **kwargs)
    return wrapper
