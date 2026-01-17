from flask import Flask
from flask_cors import CORS


def create_app(config_object='config.Config'):
    """Application factory for Flask app"""
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Initialize CORS
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})

    # Register blueprints
    from app.api.camera import camera_bp
    from app.api.llm import llm_bp

    app.register_blueprint(camera_bp, url_prefix='/api/camera')
    app.register_blueprint(llm_bp, url_prefix='/api/llm')

    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200

    return app
