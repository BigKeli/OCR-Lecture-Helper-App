from flask import Blueprint, request, jsonify, current_app
from app.models.video_processor import video_processor
from app.utils.camera_handler import camera_handler
import time
import logging

logger = logging.getLogger(__name__)
llm_bp = Blueprint('llm', __name__)


def _get_snapshot_or_error():
    """Get captured snapshot or return error response"""
    frame = camera_handler.get_snapshot()
    if frame is None:
        return None, (jsonify({
            'success': False,
            'error': 'No snapshot available. Click "Refresh Frame" to capture a snapshot first.'
        }), 400)
    return frame, None


def _process_and_respond(task: str, custom_prompt: str = None, system_prompt: str = None):
    """Common processing logic for all endpoints"""
    frame, error = _get_snapshot_or_error()
    if error:
        return error

    start_time = time.time()
    result = video_processor.process_frame(
        frame,
        task=task,
        custom_prompt=custom_prompt,
        system_prompt=system_prompt
    )
    elapsed = time.time() - start_time

    if result['success']:
        logger.info(f"Frame processed in {elapsed:.2f}s - task: {task}")
        result['processing_time'] = round(elapsed, 2)
    else:
        logger.error(f"Processing failed: {result.get('error')}")

    return jsonify(result), 200 if result['success'] else 500


@llm_bp.route('/read', methods=['POST'])
def read_text():
    """
    Read all text from current frame.

    Optional request body:
    {
        "system_prompt": "Custom system prompt to inject"
    }
    """
    data = request.get_json() or {}
    system_prompt = data.get('system_prompt')

    logger.info("Endpoint: /read")
    return _process_and_respond(task="read", system_prompt=system_prompt)


@llm_bp.route('/describe', methods=['POST'])
def describe():
    """
    Describe the content of current frame.

    Optional request body:
    {
        "system_prompt": "Custom system prompt to inject"
    }
    """
    data = request.get_json() or {}
    system_prompt = data.get('system_prompt')

    logger.info("Endpoint: /describe")
    return _process_and_respond(task="describe", system_prompt=system_prompt)


@llm_bp.route('/summarize', methods=['POST'])
def summarize():
    """
    Summarize key points from current frame.

    Optional request body:
    {
        "system_prompt": "Custom system prompt to inject"
    }
    """
    data = request.get_json() or {}
    system_prompt = data.get('system_prompt')

    logger.info("Endpoint: /summarize")
    return _process_and_respond(task="summarize", system_prompt=system_prompt)


@llm_bp.route('/custom', methods=['POST'])
def custom_query():
    """
    Process frame with custom prompt.

    Request body:
    {
        "prompt": "Your custom prompt (required)",
        "system_prompt": "Custom system prompt to inject (optional)"
    }
    """
    data = request.get_json() or {}
    custom_prompt = data.get('prompt')
    system_prompt = data.get('system_prompt')

    if not custom_prompt:
        return jsonify({
            'success': False,
            'error': 'prompt is required'
        }), 400

    logger.info("Endpoint: /custom")
    return _process_and_respond(task="custom", custom_prompt=custom_prompt, system_prompt=system_prompt)


@llm_bp.route('/process', methods=['POST'])
def process_frame():
    """
    Legacy endpoint - process frame with specified task.

    Request body:
    {
        "task": "describe" | "read" | "summarize" | "custom",
        "custom_prompt": "prompt for custom task",
        "system_prompt": "optional system prompt"
    }
    """
    data = request.get_json() or {}
    task = data.get('task', 'describe')
    custom_prompt = data.get('custom_prompt')
    system_prompt = data.get('system_prompt')

    logger.info(f"Endpoint: /process (task={task})")
    return _process_and_respond(task=task, custom_prompt=custom_prompt, system_prompt=system_prompt)


@llm_bp.route('/status', methods=['GET'])
def get_status():
    """Get LLM service status"""
    api_key_configured = bool(current_app.config.get('OPENAI_API_KEY'))

    return jsonify({
        'provider': 'openai',
        'model': current_app.config.get('OPENAI_MODEL', 'gpt-4o'),
        'api_key_configured': api_key_configured,
        'ready': api_key_configured
    }), 200
