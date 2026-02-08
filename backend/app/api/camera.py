from flask import Blueprint, Response, request, jsonify
from app.utils.camera_handler import camera_handler
import logging

logger = logging.getLogger(__name__)
camera_bp = Blueprint('camera', __name__)


@camera_bp.route('/start', methods=['POST'])
def start_ip_camera():
    """Start IP camera via RTSP"""
    try:
        data = request.get_json()
        rtsp_url = data.get('rtsp_url')

        if not rtsp_url:
            logger.warning("Camera start attempted without RTSP URL")
            return jsonify({
                'success': False,
                'error': 'rtsp_url is required'
            }), 400

        logger.info(f"Starting IP camera: {rtsp_url}")
        camera_handler.start_camera(rtsp_url)
        logger.info("IP camera started successfully")

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


@camera_bp.route('/frame')
def capture_and_get_frame():
    """Capture a fresh frame from camera and return as JPEG"""
    import cv2

    logger.info("Frame capture requested")

    # Capture a fresh frame on demand
    frame = camera_handler.capture_frame()

    if frame is None:
        logger.warning("No frame captured - camera may not be connected")
        return jsonify({
            'success': False,
            'error': 'No frame available. Please start camera first.'
        }), 404

    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

    if ret:
        logger.info(f"Frame captured and encoded - Shape: {frame.shape}")
        return Response(buffer.tobytes(), mimetype='image/jpeg')

    logger.error("Failed to encode frame as JPEG")
    return jsonify({
        'success': False,
        'error': 'Failed to encode frame'
    }), 500


@camera_bp.route('/stop', methods=['POST'])
def stop_camera():
    """Stop camera"""
    try:
        logger.info("Stopping camera")
        camera_handler.stop()
        logger.info("Camera stopped successfully")
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


@camera_bp.route('/status', methods=['GET'])
def get_camera_status():
    """Get current camera status"""
    return jsonify({
        'success': True,
        'status': camera_handler.get_status()
    }), 200


@camera_bp.route('/frame/base64', methods=['GET'])
def get_frame_base64():
    """Get current captured frame as base64 JSON (for API clients)"""
    import cv2
    import base64

    # Capture a fresh frame
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

    # Convert to base64
    img_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')

    return jsonify({
        'success': True,
        'frame': img_base64,
        'content_type': 'image/jpeg',
        'shape': {
            'height': frame.shape[0],
            'width': frame.shape[1],
            'channels': frame.shape[2]
        }
    }), 200
