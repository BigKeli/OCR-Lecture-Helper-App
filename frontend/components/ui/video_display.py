"""Video display UI component"""
import gradio as gr
import requests
import cv2
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)


def get_frame_from_stream(api_client):
    """Fetch a single frame from the MJPEG stream"""
    try:
        stream_url = api_client.get_stream_url()
        response = requests.get(stream_url, stream=True, timeout=2)

        if response.status_code == 200:
            # Read MJPEG stream - look for JPEG boundaries
            bytes_data = b""

            for chunk in response.iter_content(chunk_size=4096):
                bytes_data += chunk

                # Look for JPEG start and end markers
                a = bytes_data.find(b"\xff\xd8")  # JPEG start
                b = bytes_data.find(b"\xff\xd9")  # JPEG end

                if a != -1 and b != -1:
                    jpg = bytes_data[a : b + 2]
                    # Decode image
                    img_array = np.frombuffer(jpg, dtype=np.uint8)
                    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    if img is not None:
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        return Image.fromarray(img)
                    break

                # Limit data read
                if len(bytes_data) > 200000:
                    break
    except requests.exceptions.Timeout:
        logger.debug("Timeout fetching frame from stream")
    except Exception as e:
        logger.debug(f"Error fetching frame: {e}")

    return None


def create_placeholder_image():
    """Create a placeholder image when camera is not active"""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img.fill(40)  # Dark gray background

    # Add text using cv2
    text = "No Camera Active"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    thickness = 2
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = (640 - text_size[0]) // 2
    text_y = (480 + text_size[1]) // 2
    cv2.putText(img, text, (text_x, text_y), font, font_scale, (150, 150, 150), thickness)

    subtext = "Start a camera to see the feed"
    font_scale_sub = 0.5
    subtext_size = cv2.getTextSize(subtext, font, font_scale_sub, 1)[0]
    subtext_x = (640 - subtext_size[0]) // 2
    subtext_y = text_y + 40
    cv2.putText(img, subtext, (subtext_x, subtext_y), font, font_scale_sub, (100, 100, 100), 1)

    return Image.fromarray(img)


def build_video_display(api_client):
    """Build video display component - returns image component and update function"""

    def update_frame():
        """Fetch and return the latest frame"""
        frame = get_frame_from_stream(api_client)
        if frame is not None:
            return frame
        return create_placeholder_image()

    # Create the image component
    video_image = gr.Image(
        value=create_placeholder_image(),
        label="Camera Feed",
        type="pil",
        height=480,
    )

    return video_image, update_frame
