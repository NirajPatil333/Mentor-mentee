"""
Routes package initialization.
Exports all blueprints for registration in the Flask application factory.
"""

from routes.auth import auth_bp
from routes.mentees import mentees_bp
from routes.mentors import mentors_bp
from routes.skills import skills_bp
from routes.requests import requests_bp
from routes.sessions import sessions_bp
from routes.resources import resources_bp
from routes.progress import progress_bp
from routes.certificates import certificates_bp
from routes.achievements import achievements_bp
from routes.feedback import feedback_bp

__all__ = ['auth_bp', 'mentees_bp', 'mentors_bp', 'skills_bp', 'requests_bp', 'sessions_bp', 'resources_bp', 'progress_bp', 'certificates_bp', 'achievements_bp', 'feedback_bp']



