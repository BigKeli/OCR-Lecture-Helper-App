import cv2
import numpy as np
from threading import Thread, Lock
import time
import logging
from flask import current_app

logger = logging.getLogger(__name__)


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
        logger.info(f"Connecting to IP camera via RTSP: {rtsp_url}")

        # Explicitly use FFMPEG backend for RTSP streams
        self.camera = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

        if not self.camera.isOpened():
            raise Exception(f"Failed to connect to IP camera: {rtsp_url}")

        # Set buffer size to reduce latency for RTSP streams
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Set RTSP transport to TCP for more reliable connection
        # (UDP is default but can be unreliable on some networks)
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

        logger.info("IP camera connected successfully, starting capture thread")
        self.source_type = "ip"
        self.is_running = True
        self.thread = Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

        # Give the thread a moment to start capturing
        time.sleep(1.0)  # Increased wait time for RTSP to buffer

        # Check if we're actually getting frames
        if self.current_frame is None:
            logger.warning(
                "IP camera connected but not receiving frames yet - this might take a few more seconds"
            )
        else:
            logger.info(
                f"IP camera is capturing frames successfully - Frame shape: {self.current_frame.shape}"
            )

        return True

    def receive_phone_frame(self, frame_data):
        """Receive frame from phone via WebSocket"""
        try:
            if not frame_data or len(frame_data) == 0:
                logger.warning("Received empty frame data from phone")
                return False

            # Decode base64 or binary frame data
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                logger.warning("Failed to decode frame from phone")
                return False

            # Validate frame dimensions
            if frame.shape[0] < 100 or frame.shape[1] < 100:
                logger.warning(f"Frame too small: {frame.shape}")
                return False

            with self.lock:
                self.current_frame = frame.copy()
                self.source_type = "phone"

                # Add to queue for processing
                if not self.frame_queue.full():
                    self.frame_queue.put(frame.copy())

            return True
        except Exception as e:
            logger.error(f"Error receiving phone frame: {e}")
            return False

    def _capture_loop(self):
        """Internal loop for capturing frames from camera"""
        consecutive_failures = 0
        max_consecutive_failures = 50
        frame_count = 0

        logger.info(f"Starting capture loop for {self.source_type} camera")

        while self.is_running:
            if self.camera is not None and self.camera.isOpened():
                ret, frame = self.camera.read()

                if ret and frame is not None:
                    frame_count += 1
                    consecutive_failures = 0

                    # Log first successful frame
                    if frame_count == 1:
                        logger.info(
                            f"First frame captured successfully - Shape: {frame.shape}"
                        )
                    elif frame_count % 100 == 0:
                        logger.debug(
                            f"Captured {frame_count} frames from {self.source_type} camera"
                        )

                    with self.lock:
                        # print("frame copy : ", frame.copy())
                        self.current_frame = frame.copy()
                        # OK
                else:
                    consecutive_failures += 1

                    if consecutive_failures == 1:
                        logger.warning(
                            f"Failed to read frame from {self.source_type} camera"
                        )
                    elif consecutive_failures >= max_consecutive_failures:
                        logger.error(
                            f"Too many consecutive frame read failures ({consecutive_failures}). Camera might be disconnected."
                        )
                        self.is_running = False
                        break

                    time.sleep(0.1)
            else:
                logger.error("Camera is not opened")
                time.sleep(0.1)

        logger.info(
            f"Capture loop ended for {self.source_type} camera. Total frames: {frame_count}"
        )

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
        cv2.putText(
            blank_frame,
            "Waiting for camera...",
            (150, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )

        stream_frame_count = 0
        last_log_time = time.time()

        while True:
            print("DEBUG: about to call get_current_frame", flush=True)
            frame = self.get_current_frame()

            if frame is None:
                frame = blank_frame
            else:
                stream_frame_count += 1

                # Log streaming status every 5 seconds
                current_time = time.time()
                if current_time - last_log_time >= 5:
                    logger.debug(
                        f"MJPEG stream active - {stream_frame_count} frames sent"
                    )
                    last_log_time = current_time

            try:
                ret, buffer = cv2.imencode(
                    ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85]
                )
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                    )
                else:
                    logger.error("Failed to encode frame as JPEG")
            except Exception as e:
                logger.error(f"JPEG encoding failed: {e}")

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
