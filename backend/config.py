"""
Configuration settings for the Flask application.
Keeping configuration separate from application logic allows for easy
switching between environments (development, testing, production).
"""

import os
import urllib.parse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    # Secret key used for session security and cryptographic signing
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Port to run the server on
    PORT = int(os.environ.get('PORT', 5000))
    
    # Enable debug mode for local development (provides hot reload and detailed error tracing)
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')

    # Database configuration from environment variables
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'mentor_mentee_db')

    # Safely handle special characters in database password
    _encoded_password = urllib.parse.quote_plus(DB_PASSWORD) if DB_PASSWORD else ''

    # PyMySQL connection URI: mysql+pymysql://<user>:<password>@<host>:<port>/<db_name>
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL')
        or f"mysql+pymysql://{DB_USER}:{_encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # Disable Flask-SQLAlchemy event system modification tracking to save resources
    SQLALCHEMY_TRACK_MODIFICATIONS = False

