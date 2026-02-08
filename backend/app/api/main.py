"""
Main API endpoints for the Assistive Classroom app.
Simplified interface for capture, analysis, and notes.
"""
from flask import Blueprint, request, jsonify
from app.utils.camera_handler import camera_handler
from app.models.video_processor import video_processor
from flask import current_app
import cv2
import base64
import uuid
from datetime import datetime
import logging
import json
import os

logger = logging.getLogger(__name__)
main_bp = Blueprint('main', __name__)

# Notes storage directory
NOTES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'notes')


def ensure_notes_dir():
    """Create notes directory if it doesn't exist"""
    if not os.path.exists(NOTES_DIR):
        os.makedirs(NOTES_DIR)
        logger.info(f"Created notes directory: {NOTES_DIR}")


def load_all_notes():
    """Load all notes from the notes directory"""
    ensure_notes_dir()
    notes = []
    for filename in os.listdir(NOTES_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(NOTES_DIR, filename)
            try:
                with open(filepath, 'r') as f:
                    note = json.load(f)
                    notes.append(note)
            except Exception as e:
                logger.error(f"Failed to load note {filename}: {e}")
    # Sort by created_at descending
    notes.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return notes


def save_note_to_file(note):
    """Save a note to a JSON file"""
    ensure_notes_dir()
    filepath = os.path.join(NOTES_DIR, f"{note['id']}.json")
    with open(filepath, 'w') as f:
        json.dump(note, f, indent=2)
    logger.info(f"Note saved to: {filepath}")


def delete_note_file(note_id):
    """Delete a note file"""
    filepath = os.path.join(NOTES_DIR, f"{note_id}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
        logger.info(f"Note deleted: {filepath}")
        return True
    return False


def get_note_by_id(note_id):
    """Get a single note by ID"""
    filepath = os.path.join(NOTES_DIR, f"{note_id}.json")
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None


@main_bp.route('/capture', methods=['POST'])
def capture():
    """
    Take a screenshot from the camera.

    Returns:
        JSON with base64 image data
    """
    try:
        frame = camera_handler.capture_frame()

        if frame is None:
            return jsonify({
                'success': False,
                'error': 'No frame available. Please start camera first.'
            }), 404

        # Encode as JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

        if not ret:
            return jsonify({
                'success': False,
                'error': 'Failed to encode frame'
            }), 500

        img_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')

        logger.info(f"Frame captured - Shape: {frame.shape}")

        return jsonify({
            'success': True,
            'image': img_base64,
            'content_type': 'image/jpeg',
            'width': frame.shape[1],
            'height': frame.shape[0],
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Capture failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main_bp.route('/read-text', methods=['POST'])
def read_text():
    """
    Perform OCR analysis on the current captured frame.

    Request body (optional):
        {
            "provider": "ollama" | "openai" | "claude"
        }

    Returns:
        JSON with extracted text
    """
    try:
        data = request.get_json() or {}
        provider = data.get('provider', current_app.config.get('DEFAULT_LLM_PROVIDER', 'ollama'))

        frame = camera_handler.get_current_frame()

        if frame is None:
            return jsonify({
                'success': False,
                'error': 'No frame available. Please capture an image first.'
            }), 404

        result = video_processor.process_frame(
            frame,
            task='read',
            provider=provider
        )

        if result['success']:
            return jsonify({
                'success': True,
                'text': result['text'],
                'provider': result.get('provider'),
                'model': result.get('model')
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'OCR analysis failed')
            }), 500

    except Exception as e:
        logger.error(f"Read text failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main_bp.route('/describe', methods=['POST'])
def describe():
    """
    Get an image description of the current captured frame.

    Request body (optional):
        {
            "provider": "ollama" | "openai" | "claude"
        }

    Returns:
        JSON with image description
    """
    try:
        data = request.get_json() or {}
        provider = data.get('provider', current_app.config.get('DEFAULT_LLM_PROVIDER', 'ollama'))

        frame = camera_handler.get_current_frame()

        if frame is None:
            return jsonify({
                'success': False,
                'error': 'No frame available. Please capture an image first.'
            }), 404

        result = video_processor.process_frame(
            frame,
            task='describe',
            provider=provider
        )

        if result['success']:
            return jsonify({
                'success': True,
                'description': result['text'],
                'provider': result.get('provider'),
                'model': result.get('model')
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Description failed')
            }), 500

    except Exception as e:
        logger.error(f"Describe failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main_bp.route('/summarize', methods=['POST'])
def summarize():
    """
    Get a summary of the current captured frame.

    Request body (optional):
        {
            "provider": "ollama" | "openai" | "claude"
        }

    Returns:
        JSON with summary
    """
    try:
        data = request.get_json() or {}
        provider = data.get('provider', current_app.config.get('DEFAULT_LLM_PROVIDER', 'ollama'))

        frame = camera_handler.get_current_frame()

        if frame is None:
            return jsonify({
                'success': False,
                'error': 'No frame available. Please capture an image first.'
            }), 404

        result = video_processor.process_frame(
            frame,
            task='summarize',
            provider=provider
        )

        if result['success']:
            return jsonify({
                'success': True,
                'summary': result['text'],
                'provider': result.get('provider'),
                'model': result.get('model')
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Summary failed')
            }), 500

    except Exception as e:
        logger.error(f"Summarize failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main_bp.route('/notes', methods=['GET'])
def get_notes():
    """
    List all saved notes.

    Returns:
        JSON with list of notes
    """
    notes = load_all_notes()
    return jsonify({
        'success': True,
        'notes': notes,
        'count': len(notes)
    }), 200


@main_bp.route('/notes', methods=['POST'])
def save_note():
    """
    Save a new note.

    Request body:
        {
            "title": "Note title",
            "content": "Note content",
            "type": "read" | "describe" | "summarize" | "custom",
            "image": "base64 image data" (optional)
        }

    Returns:
        JSON with saved note
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400

        if not data.get('content'):
            return jsonify({
                'success': False,
                'error': 'Note content is required'
            }), 400

        note = {
            'id': str(uuid.uuid4()),
            'title': data.get('title', 'Untitled Note'),
            'content': data.get('content'),
            'type': data.get('type', 'custom'),
            'image': data.get('image'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # Save to file
        save_note_to_file(note)

        return jsonify({
            'success': True,
            'note': note
        }), 201

    except Exception as e:
        logger.error(f"Save note failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main_bp.route('/notes/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    """
    Delete a note by ID.

    Returns:
        JSON with success status
    """
    if delete_note_file(note_id):
        return jsonify({
            'success': True,
            'message': f'Note {note_id} deleted'
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': f'Note {note_id} not found'
        }), 404


@main_bp.route('/notes/<note_id>', methods=['GET'])
def get_note(note_id):
    """
    Get a single note by ID.

    Returns:
        JSON with note data
    """
    note = get_note_by_id(note_id)
    if note:
        return jsonify({
            'success': True,
            'note': note
        }), 200

    return jsonify({
        'success': False,
        'error': f'Note {note_id} not found'
    }), 404
