import cv2
import numpy as np
from threading import Thread, Lock
import time
import logging


class CameraHandler:
    """Handles video input from RTSP/IP camera"""

    def __init__(self):
        self.camera = None
        self.rtsp_url = None
        self.current_frame = None
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
        print("DEBUG: _capture_loop started")
        frame_count = 0
        while self.is_running:
            if self.camera is not None and self.camera.isOpened():
                ret, frame = self.camera.read()
                if ret:
                    frame_count += 1
                    if frame_count % 30 == 1:  # Print every 30 frames
                        print(f"DEBUG: Captured frame #{frame_count}")
                    # frameCounter += 1
                    # print(f"frame : {frame}")
                    with self.lock:
                        # print("frame copy : ", frame.copy())
                        self.current_frame = frame.copy()
                        # OK
                else:
                    print("Failed to read frame")
                    time.sleep(0.1)
            else:
                time.sleep(0.1)

    def get_current_frame(self):
        """Get the most recent frame"""
        print(f"self-lock : {self.lock}")
        with self.lock:
            if self.current_frame is not None:
                print(
                    f"DEBUG: get_current_frame returning frame with shape {self.current_frame.shape}",
                    flush=True,
                )
                return self.current_frame.copy()
            else:
                print("DEBUG: get_current_frame - current_frame is None", flush=True)
        return None

    def generate_mjpeg_stream(self):
        """Generate MJPEG stream for web display"""
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        print("DEBUG: generate_mjpeg_stream started", flush=True)
        while True:
            print("DEBUG: about to call get_current_frame", flush=True)
            frame = self.get_current_frame()

            if frame is None:
                frame = blank_frame

            try:
                ret, buffer = cv2.imencode(
                    ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85]
                )
                if ret:
                    frame_bytes = buffer.tobytes()
                    print(f"DEBUG: yielding frame, size={len(frame_bytes)} bytes", flush=True)
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                    )
                else:
                    print("DEBUG: cv2.imencode failed", flush=True)
            except Exception as e:
                print(f"JPEG encoding failed: {e}", flush=True)

            time.sleep(0.033)  # ~30 FPS

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

        self.rtsp_url = None

    def get_status(self):
        """Get camera status"""
        return {
            "is_running": self.is_running,
            "rtsp_url": self.rtsp_url,
            "has_frame": self.current_frame is not None,
        }


# Global camera handler instance
camera_handler = CameraHandler()
