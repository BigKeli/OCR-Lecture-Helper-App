from flask import Flask, render_template
from flask_cors import CORS
import os


def create_app(config_object='config.Config'):
    """Application factory for Flask app"""
    # Get the frontend folder path
    # __file__ = backend/app/__init__.py
    # Go up twice to get to backend/, then up once more to project root
    app_dir = os.path.dirname(os.path.abspath(__file__))  # backend/app
    backend_dir = os.path.dirname(app_dir)                 # backend
    project_root = os.path.dirname(backend_dir)            # OCR-Lecture-Helper-App
    frontend_dir = os.path.join(project_root, 'frontend')

    app = Flask(
        __name__,
        template_folder=os.path.join(frontend_dir, 'templates'),
        static_folder=os.path.join(frontend_dir, 'static'),
        static_url_path='/static'
    )
    app.config.from_object(config_object)

    # Initialize CORS
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})

    # Register blueprints
    from app.api.camera import camera_bp
    from app.api.llm import llm_bp
    from app.api.settings import settings_bp
    from app.api.main import main_bp

    app.register_blueprint(camera_bp, url_prefix='/api/camera')
    app.register_blueprint(llm_bp, url_prefix='/api/llm')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(main_bp, url_prefix='/api')

    # Frontend routes
    @app.route('/')
    def index():
        """Serve the main frontend page"""
        return render_template('index.html')

    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200

    return app
