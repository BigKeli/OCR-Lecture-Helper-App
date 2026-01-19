from flask import Blueprint, Response, request, jsonify
from app.utils.camera_handler import camera_handler
import cv2
import logging

logger = logging.getLogger(__name__)
camera_bp = Blueprint('camera', __name__)


@camera_bp.route('/start', methods=['POST'])
def start_camera():
    """Start RTSP camera"""
    try:
        data = request.get_json()
        rtsp_url = data.get('rtsp_url')

        if not rtsp_url:
            return jsonify({
                'success': False,
                'error': 'rtsp_url is required'
            }), 400

        logger.info(f"Starting camera: {rtsp_url}")
        camera_handler.start_camera(rtsp_url)
        logger.info("Camera started successfully")

        return jsonify({
            'success': True,
            'message': 'Camera started',
            'status': camera_handler.get_status()
        }), 200

    except Exception as e:
        logger.error(f"Failed to start camera: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@camera_bp.route('/capture', methods=['POST'])
def capture_snapshot():
    """Capture current frame as snapshot for LLM processing"""
    success = camera_handler.capture_snapshot()

    if success:
        logger.info("Snapshot captured")
        return jsonify({
            'success': True,
            'message': 'Snapshot captured'
        }), 200
    else:
        logger.warning("No frame available to capture")
        return jsonify({
            'success': False,
            'error': 'No frame available. Start camera first.'
        }), 400


@camera_bp.route('/frame')
def get_frame():
    """Get the captured snapshot as JPEG"""
    frame = camera_handler.get_snapshot()

    if frame is None:
        # Fallback to current frame if no snapshot
        frame = camera_handler.get_current_frame()

    if frame is None:
        return "No frame available", 404

    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if ret:
        return Response(buffer.tobytes(), mimetype='image/jpeg')
    return "Encoding failed", 500


@camera_bp.route('/status')
def get_status():
    """Get camera status"""
    return jsonify(camera_handler.get_status()), 200


@camera_bp.route('/stop', methods=['POST'])
def stop_camera():
    """Stop camera"""
    try:
        logger.info("Stopping camera")
        camera_handler.stop()
        logger.info("Camera stopped")
        return jsonify({
            'success': True,
            'message': 'Camera stopped'
        }), 200

    except Exception as e:
        logger.error(f"Failed to stop camera: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
