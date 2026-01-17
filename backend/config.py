import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Flask settings
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 5000))

    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')

    # Camera settings
    CAMERA_WIDTH = int(os.environ.get('CAMERA_WIDTH', 1280))
    CAMERA_HEIGHT = int(os.environ.get('CAMERA_HEIGHT', 720))
    CAMERA_FPS = int(os.environ.get('CAMERA_FPS', 30))

    # LLM settings
    DEFAULT_LLM_PROVIDER = os.environ.get('DEFAULT_LLM_PROVIDER', 'local')  # local, openai, claude

    # Local LLM settings
    LOCAL_MODEL_NAME = os.environ.get('LOCAL_MODEL_NAME', 'Salesforce/blip-image-captioning-base')
    LOCAL_MODEL_DEVICE = os.environ.get('LOCAL_MODEL_DEVICE', 'cpu')  # cpu or cuda

    # OpenAI settings
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o')

    # Claude settings
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')
    CLAUDE_MODEL = os.environ.get('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')

    # Processing settings
    FRAME_PROCESS_INTERVAL = int(os.environ.get('FRAME_PROCESS_INTERVAL', 2))  # seconds between processing frames
    MAX_FRAME_QUEUE = int(os.environ.get('MAX_FRAME_QUEUE', 100))
