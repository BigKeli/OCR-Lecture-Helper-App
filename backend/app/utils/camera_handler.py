import cv2
import numpy as np
from threading import Thread, Lock
import queue
import time
from flask import current_app


class CameraHandler:
    """Handles video input from laptop camera, phone, or IP camera"""

    def __init__(self):
        self.camera = None
        self.source_type = None  # 'laptop', 'phone', 'ip'
        self.frame_queue = queue.Queue(maxsize=100)
        self.current_frame = None
        self.is_running = False
        self.lock = Lock()
        self.thread = None

    def start_laptop_camera(self, camera_index=0):
        """Start laptop camera capture"""
        self.stop()
        self.camera = cv2.VideoCapture(camera_index)

        if not self.camera.isOpened():
            raise Exception(f"Failed to open camera {camera_index}")

        # Set camera properties
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, current_app.config['CAMERA_WIDTH'])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, current_app.config['CAMERA_HEIGHT'])
        self.camera.set(cv2.CAP_PROP_FPS, current_app.config['CAMERA_FPS'])

        self.source_type = 'laptop'
        self.is_running = True
        self.thread = Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        return True

    def start_ip_camera(self, rtsp_url):
        """Start IP camera capture via RTSP"""
        self.stop()
        self.camera = cv2.VideoCapture(rtsp_url)

        if not self.camera.isOpened():
            raise Exception(f"Failed to connect to IP camera: {rtsp_url}")

        self.source_type = 'ip'
        self.is_running = True
        self.thread = Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        return True

    def receive_phone_frame(self, frame_data):
        """Receive frame from phone via WebSocket"""
        try:
            if not frame_data or len(frame_data) == 0:
                print("Received empty frame data from phone")
                return False

            # Decode base64 or binary frame data
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                print("Failed to decode frame from phone")
                return False

            # Validate frame dimensions
            if frame.shape[0] < 100 or frame.shape[1] < 100:
                print(f"Frame too small: {frame.shape}")
                return False

            with self.lock:
                self.current_frame = frame.copy()
                self.source_type = 'phone'

                # Add to queue for processing
                if not self.frame_queue.full():
                    self.frame_queue.put(frame.copy())

            return True
        except Exception as e:
            print(f"Error receiving phone frame: {e}")
            return False

    def _capture_loop(self):
        """Internal loop for capturing frames from camera"""
        while self.is_running:
            if self.camera is not None and self.camera.isOpened():
                ret, frame = self.camera.read()

                if ret:
                    with self.lock:
                        self.current_frame = frame.copy()

                    # Add to queue for processing
                    if not self.frame_queue.full():
                        self.frame_queue.put(frame.copy())
                else:
                    print("Failed to read frame")
                    time.sleep(0.1)
            else:
                time.sleep(0.1)

    def get_current_frame(self):
        """Get the most recent frame"""
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
        return None

    def get_frame_for_processing(self, timeout=1):
        """Get frame from queue for LLM processing"""
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def generate_mjpeg_stream(self):
        """Generate MJPEG stream for web display"""
        # Create a blank frame as fallback
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)

        while True:
            frame = self.get_current_frame()

            if frame is None:
                frame = blank_frame

            try:
                # Encode frame as JPEG with quality setting
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            except Exception as e:
                print(f"JPEG encoding failed: {e}")

            time.sleep(0.033)  # ~30 FPS

    def stop(self):
        """Stop camera capture"""
        self.is_running = False

        if self.thread is not None:
            self.thread.join(timeout=2)

        if self.camera is not None:
            self.camera.release()
            self.camera = None

        # Clear queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break

        with self.lock:
            self.current_frame = None

        self.source_type = None

    def get_status(self):
        """Get camera status"""
        return {
            'is_running': self.is_running,
            'source_type': self.source_type,
            'has_frame': self.current_frame is not None
        }


# Global camera handler instance
camera_handler = CameraHandler()
