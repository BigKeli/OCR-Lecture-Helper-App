from flask import Blueprint, request, jsonify, current_app
from app.models.video_processor import video_processor
from app.utils.camera_handler import camera_handler
import time
import logging

logger = logging.getLogger(__name__)
llm_bp = Blueprint('llm', __name__)


@llm_bp.route('/process', methods=['POST'])
def process_frame():
    """
    Process current frame with LLM

    Request body:
    {
        "task": "describe" | "read" | "summarize" | "custom",
        "provider": "local" | "openai" | "claude" (optional),
        "custom_prompt": "your prompt" (optional, for custom task)
    }
    """
    try:
        data = request.get_json()
        task = data.get('task', 'describe')
        provider = data.get('provider')
        custom_prompt = data.get('custom_prompt')

        logger.info(f"Processing frame - Task: {task}, Provider: {provider or 'default'}")

        frame = camera_handler.get_current_frame()

        if frame is None:
            logger.warning("Frame processing requested but no frame available")
            return jsonify({
                'success': False,
                'error': 'No frame available. Please start camera first.'
            }), 400

        start_time = time.time()
        result = video_processor.process_frame(
            frame,
            task=task,
            provider=provider,
            custom_prompt=custom_prompt
        )
        elapsed = time.time() - start_time

        if result['success']:
            logger.info(f"Frame processed in {elapsed:.2f}s using {result.get('provider', 'unknown')}")
        else:
            logger.error(f"Frame processing failed: {result.get('error', 'unknown')}")

        return jsonify(result), 200 if result['success'] else 500

    except Exception as e:
        logger.error(f"Exception during frame processing: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@llm_bp.route('/providers', methods=['GET'])
def get_providers():
    """Get available LLM providers and their status"""
    providers = {
        'local': {
            'available': True,
            'model': current_app.config['LOCAL_MODEL_NAME'],
            'device': current_app.config['LOCAL_MODEL_DEVICE']
        },
        'openai': {
            'available': bool(current_app.config.get('OPENAI_API_KEY')),
            'model': current_app.config['OPENAI_MODEL']
        },
        'claude': {
            'available': bool(current_app.config.get('CLAUDE_API_KEY')),
            'model': current_app.config['CLAUDE_MODEL']
        }
    }

    return jsonify({
        'providers': providers,
        'default': current_app.config['DEFAULT_LLM_PROVIDER']
    }), 200


@llm_bp.route('/tasks', methods=['GET'])
def get_available_tasks():
    """Get available processing tasks"""
    tasks = {
        'describe': 'Describe the content of the slide/board',
        'read': 'Read all text on the slide/board',
        'summarize': 'Summarize key points in bullet points',
        'custom': 'Use a custom prompt'
    }

    return jsonify({'tasks': tasks}), 200
