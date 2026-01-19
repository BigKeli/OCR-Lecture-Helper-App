import cv2
from threading import Thread, Lock
import time


class CameraHandler:
    """Handles video input from RTSP/IP camera"""

    def __init__(self):
        self.camera = None
        self.rtsp_url = None
        self.current_frame = None
        self.captured_snapshot = None  # Snapshot for LLM processing
        self.is_running = False
        self.lock = Lock()
        self.thread = None

    def start_camera(self, rtsp_url):
        """Start camera capture via RTSP URL"""
        self.stop()
        self.rtsp_url = rtsp_url
        self.camera = cv2.VideoCapture(rtsp_url)

        if not self.camera.isOpened():
            raise Exception(f"Failed to connect to camera: {rtsp_url}")
        self.is_running = True
        self.thread = Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        return True

    def _capture_loop(self):
        """Internal loop for capturing frames from camera"""
        while self.is_running:
            if self.camera is not None and self.camera.isOpened():
                ret, frame = self.camera.read()
                if ret:
                    with self.lock:
                        self.current_frame = frame.copy()
                else:
                    time.sleep(0.1)
            else:
                time.sleep(0.1)

    def get_current_frame(self):
        """Get the most recent frame from live feed"""
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
        return None

    def capture_snapshot(self):
        """Capture current frame as snapshot for LLM processing"""
        with self.lock:
            if self.current_frame is not None:
                self.captured_snapshot = self.current_frame.copy()
                # Debug: print hash of snapshot to verify it changed
                import hashlib
                frame_hash = hashlib.md5(self.captured_snapshot.tobytes()).hexdigest()[:8]
                print(f"DEBUG: Snapshot captured, hash={frame_hash}", flush=True)
                return True
        return False

    def get_snapshot(self):
        """Get the captured snapshot for LLM processing"""
        with self.lock:
            if self.captured_snapshot is not None:
                import hashlib
                frame_hash = hashlib.md5(self.captured_snapshot.tobytes()).hexdigest()[:8]
                print(f"DEBUG: Returning snapshot, hash={frame_hash}", flush=True)
                return self.captured_snapshot.copy()
        return None

    def stop(self):
        """Stop camera capture"""
        self.is_running = False

        if self.thread is not None:
            self.thread.join(timeout=2)

        if self.camera is not None:
            self.camera.release()
            self.camera = None

        with self.lock:
            self.current_frame = None
            self.captured_snapshot = None

        self.rtsp_url = None

    def get_status(self):
        """Get camera status"""
        return {
            "is_running": self.is_running,
            "rtsp_url": self.rtsp_url,
            "has_frame": self.current_frame is not None,
            "has_snapshot": self.captured_snapshot is not None,
        }


# Global camera handler instance
camera_handler = CameraHandler()
