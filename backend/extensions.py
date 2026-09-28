"""
Database and extension instances.
Keeping extensions in a dedicated file avoids circular import issues
when models and application factory need access to the same instance.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

# Initialize Flask-SQLAlchemy instance
db = SQLAlchemy()

# Initialize Flask-JWT-Extended instance
jwt = JWTManager()

