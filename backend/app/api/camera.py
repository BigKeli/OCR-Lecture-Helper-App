from flask import Blueprint, Response, request, jsonify
from app.utils.camera_handler import camera_handler
import base64
import logging

logger = logging.getLogger(__name__)
camera_bp = Blueprint('camera', __name__)


@camera_bp.route('/start/laptop', methods=['POST'])
def start_laptop_camera():
    """Start laptop camera"""
    try:
        data = request.get_json() or {}
        camera_index = data.get('camera_index', 0)

        logger.info(f"Starting laptop camera {camera_index}")
        camera_handler.start_laptop_camera(camera_index)
        logger.info(f"Laptop camera {camera_index} started successfully")

        return jsonify({
            'success': True,
            'message': f'Laptop camera {camera_index} started',
            'status': camera_handler.get_status()
        }), 200

    except Exception as e:
        logger.error(f"Failed to start laptop camera: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@camera_bp.route('/start/ip', methods=['POST'])
def start_ip_camera():
    """Start IP camera via RTSP"""
    try:
        data = request.get_json()
        rtsp_url = data.get('rtsp_url')

        if not rtsp_url:
            logger.warning("IP camera start attempted without RTSP URL")
            return jsonify({
                'success': False,
                'error': 'rtsp_url is required'
            }), 400

        logger.info(f"Starting IP camera: {rtsp_url}")
        camera_handler.start_ip_camera(rtsp_url)
        logger.info("IP camera started successfully")

        return jsonify({
            'success': True,
            'message': 'IP camera started',
            'status': camera_handler.get_status()
        }), 200

    except Exception as e:
        logger.error(f"Failed to start IP camera: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@camera_bp.route('/phone/frame', methods=['POST'])
def receive_phone_frame():
    """Receive frame from phone camera via POST"""
    try:
        # Check if binary data or JSON with base64
        if request.content_type == 'application/octet-stream':
            frame_data = request.data
        else:
            data = request.get_json()
            frame_base64 = data.get('frame')
            if not frame_base64:
                logger.warning("Phone frame received without data")
                return jsonify({
                    'success': False,
                    'error': 'frame data is required'
                }), 400

            # Decode base64
            frame_data = base64.b64decode(frame_base64)

        success = camera_handler.receive_phone_frame(frame_data)

        # Don't log every frame - too verbose
        return jsonify({
            'success': success,
            'status': camera_handler.get_status()
        }), 200

    except Exception as e:
        logger.error(f"Error receiving phone frame: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@camera_bp.route('/stream')
def video_stream():
    """Stream video as MJPEG"""
    logger.info("Video stream requested")
    return Response(
        camera_handler.generate_mjpeg_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


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
