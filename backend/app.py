from flask import Flask, jsonify
from config import Config

def create_app():
    """
    Application factory function.
    Creates and configures the Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

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
