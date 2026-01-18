"""Camera service for detecting and managing cameras"""
import cv2
import logging

logger = logging.getLogger(__name__)


class CameraService:
    """Service for camera detection and management"""
    
    @staticmethod
    def detect_available_cameras(max_cameras=5):
        """Detect available camera indices"""
        available = []
        for i in range(max_cameras):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    # Try to read a frame to confirm it's working
                    ret, _ = cap.read()
                    if ret:
                        available.append(i)
                cap.release()
            except Exception as e:
                logger.debug(f"Camera {i} not available: {e}")
                continue
        
        return available
    
    @staticmethod
    def get_camera_dropdown_options(max_cameras=5):
        """Get dropdown options for available cameras"""
        cameras = CameraService.detect_available_cameras(max_cameras)
        if not cameras:
            # Fallback: return default camera index
            return [("Camera 0", 0)]
        
        options = [(f"Camera {i}", i) for i in cameras]
        return options
