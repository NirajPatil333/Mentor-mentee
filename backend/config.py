"""
Configuration settings for the Flask application.
Keeping configuration separate from application logic allows for easy
switching between environments (development, testing, production).
"""

import os

class Config:
    # Secret key used for session security and cryptographic signing
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Port to run the server on
    PORT = int(os.environ.get('PORT', 5000))
    
    # Enable debug mode for local development (provides hot reload and detailed error tracing)
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')
