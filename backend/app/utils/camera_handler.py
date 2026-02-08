import cv2
from threading import Lock, Thread
import time
import logging
from flask import current_app

logger = logging.getLogger(__name__)


class CameraHandler:
    """Handles video input from RTSP/IP camera"""

    def __init__(self):
        self.camera = None
        self.rtsp_url = None
        self.current_frame = None      # Continuously updated by background thread
        self.captured_frame = None     # Only updated when user clicks Refresh
        self.is_running = False
        self.lock = Lock()
        self.thread = None

    def start_camera(self, rtsp_url):
        """Start camera with continuous background capture"""
        self.stop()
        self.rtsp_url = rtsp_url
        logger.info(f"Connecting to IP camera via RTSP: {rtsp_url}")

        # Explicitly use FFMPEG backend for RTSP streams
        self.camera = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

        if not self.camera.isOpened():
            raise Exception(f"Failed to connect to IP camera: {rtsp_url}")

        # Set buffer size to reduce latency for RTSP streams
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Set RTSP transport to TCP for more reliable connection
        self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"H264"))

        # Try to set reasonable resolution if possible
        try:
            self.camera.set(
                cv2.CAP_PROP_FRAME_WIDTH, current_app.config.get("CAMERA_WIDTH", 1280)
            )
            self.camera.set(
                cv2.CAP_PROP_FRAME_HEIGHT, current_app.config.get("CAMERA_HEIGHT", 720)
            )
        except:
            pass  # Some IP cameras don't allow setting resolution

        logger.info("IP camera connected, starting background capture")
        self.is_running = True
        self.thread = Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

        # Wait for first frame
        time.sleep(1.0)

        if self.current_frame is not None:
            # Auto-capture first frame
            self.capture_frame()
            logger.info(f"IP camera ready - Frame shape: {self.current_frame.shape}")
        else:
            logger.warning("IP camera connected but not receiving frames yet")

        return True

    def _capture_loop(self):
        """Background loop to continuously read frames (keeps RTSP alive)"""
        while self.is_running:
            if self.camera is not None and self.camera.isOpened():
                ret, frame = self.camera.read()
                if ret and frame is not None:
                    with self.lock:
                        self.current_frame = frame.copy()
                else:
                    time.sleep(0.1)
            else:
                time.sleep(0.1)

    def capture_frame(self):
        """Capture the current frame for LLM processing (called on Refresh)"""
        with self.lock:
            if self.current_frame is not None:
                self.captured_frame = self.current_frame.copy()
                logger.info(f"Frame captured for LLM - Shape: {self.captured_frame.shape}")
                return self.captured_frame
            else:
                logger.warning("No frame available to capture")
                return None

    def get_current_frame(self):
        """Get the captured frame (used by LLM)"""
        with self.lock:
            if self.captured_frame is not None:
                return self.captured_frame.copy()
        return None

    def get_live_frame(self):
        """Get the latest live frame (for streaming if needed)"""
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
        return None

    def stop(self):
        """Stop camera and release resources"""
        self.is_running = False

        if self.thread is not None:
            self.thread.join(timeout=2)
            self.thread = None

        if self.camera is not None:
            self.camera.release()
            self.camera = None

        with self.lock:
            self.current_frame = None
            self.captured_frame = None

        self.rtsp_url = None
        logger.info("Camera stopped and resources released")

    def get_status(self):
        """Get camera status"""
        return {
            "is_running": self.is_running,
            "rtsp_url": self.rtsp_url,
            "has_frame": self.current_frame is not None,
            "has_captured_frame": self.captured_frame is not None,
        }


# Global camera handler instance
camera_handler = CameraHandler()
