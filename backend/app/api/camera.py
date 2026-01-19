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


@camera_bp.route('/stream')
def video_stream():
    """Stream video as MJPEG"""
    print("DEBUG: /stream endpoint hit", flush=True)
    logger.info("Video stream requested")

    gen = camera_handler.generate_mjpeg_stream()
    print(f"DEBUG: generator created: {gen}", flush=True)

    resp = Response(
        gen,
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@camera_bp.route('/frame')
def single_frame():
    """Get a single JPEG frame"""
    import cv2
    import numpy as np

    frame = camera_handler.get_current_frame()
    if frame is None:
        return "No frame available", 404

    # Debug frame data
    print(f"DEBUG /frame: shape={frame.shape}, dtype={frame.dtype}", flush=True)
    print(f"DEBUG /frame: min={np.min(frame)}, max={np.max(frame)}, mean={np.mean(frame):.2f}", flush=True)

    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(f"DEBUG /frame: imencode ret={ret}, buffer size={len(buffer) if ret else 'N/A'}", flush=True)

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
