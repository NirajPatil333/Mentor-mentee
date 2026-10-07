from flask import Flask, jsonify
from config import Config
from extensions import db, jwt
from flask_cors import CORS
from routes import (
    auth_bp, mentees_bp, mentors_bp, skills_bp, requests_bp,
    sessions_bp, resources_bp, progress_bp, certificates_bp, achievements_bp,
    feedback_bp
)
from models import (
    User, MentorProfile, MenteeProfile, Skill,
    UserSkill, LearningInterest, MentorAvailability, MentorshipRequest,
    Session, Resource, Progress, Feedback, Certificate, Achievement
)

def create_app():
    """
    Application factory function.
    Creates and configures the Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    # Bind SQLAlchemy to the Flask application
    db.init_app(app)

    # Bind Flask-JWT-Extended to the Flask application
    jwt.init_app(app)

    # JWT custom error response handlers
    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        return jsonify({
            "status": "error",
            "message": "Missing authorization token or header"
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(callback):
        return jsonify({
            "status": "error",
            "message": "Invalid authentication token"
        }), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "status": "error",
            "message": "Authentication token has expired"
        }), 401

    # Register application blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(mentees_bp, url_prefix='/api/mentees')
    app.register_blueprint(mentors_bp, url_prefix='/api/mentors')
    app.register_blueprint(skills_bp, url_prefix='/api/skills')
    app.register_blueprint(requests_bp, url_prefix='/api/requests')
    app.register_blueprint(sessions_bp, url_prefix='/api/sessions')
    app.register_blueprint(resources_bp, url_prefix='/api/resources')
    app.register_blueprint(progress_bp, url_prefix='/api/progress')
    app.register_blueprint(certificates_bp, url_prefix='/api/certificates')
    app.register_blueprint(achievements_bp, url_prefix='/api/achievements')
    app.register_blueprint(feedback_bp, url_prefix='/api/feedback')


    # Health check route to verify that the backend is alive and responding
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            "status": "success",
            "message": "Mentor-Mentee API is running"
        }), 200

    return app


app = create_app()

if __name__ == '__main__':
    # Starts the local development server on port 5000
    app.run(
        host='127.0.0.1',
        port=Config.PORT,
        debug=Config.DEBUG
    )
