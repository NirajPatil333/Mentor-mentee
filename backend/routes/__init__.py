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

__all__ = ['auth_bp', 'mentees_bp', 'mentors_bp', 'skills_bp', 'requests_bp', 'sessions_bp']



