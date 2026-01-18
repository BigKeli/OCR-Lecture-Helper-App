"""Camera control UI components"""
import gradio as gr
from components.services.camera_service import CameraService
import socket
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:6969")


def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"


# def get_phone_url():
#     """Get phone camera URL with network IP"""
#     parsed = urlparse(BACKEND_URL)
#     hostname = parsed.hostname
#     port = parsed.port or (443 if parsed.scheme == 'https' else 80)
#     if hostname in ["localhost", "127.0.0.1"]:
#         local_ip = get_local_ip()
#         return f"{parsed.scheme}://{local_ip}:{port}/phone"
#     return f"{BACKEND_URL}/phone"


def build_camera_controls(api_client, start_laptop_fn, start_ip_fn, stop_fn):
    """Build camera control UI section"""
    # Get available cameras
    camera_options = CameraService.get_camera_dropdown_options()
    camera_labels = [opt[0] for opt in camera_options]
    camera_values = [opt[1] for opt in camera_options]
    
    with gr.Accordion("Camera Settings", open=True):
        with gr.Tab("Laptop Camera"):
            camera_dropdown = gr.Dropdown(
                choices=camera_labels,
                value=camera_labels[0] if camera_labels else None,
                label="Select Camera",
                interactive=True
            )
            start_laptop_btn = gr.Button("Start Camera", variant="primary")
        
        with gr.Tab("IP Camera"):
            rtsp_url = gr.Textbox(
                label="RTSP URL",
                placeholder="rtsp://username:password@ip:port/stream",
                lines=1
            )
            start_ip_btn = gr.Button("Start IP Camera", variant="primary")
        
        # with gr.Tab("Phone Camera"):
        #     phone_url = get_phone_url()
        #     gr.Markdown(f"**Open this URL on your phone:**\n\n`{phone_url}`")
        #     gr.Markdown(
        #         "⚠️ **Note:** HTTPS may be required for camera access. "
        #         "Use laptop camera for testing."
        #     )
        
        stop_btn = gr.Button("Stop Camera", variant="stop", size="sm")
    
    camera_status = gr.Textbox(
        label="Status",
        value="No camera active",
        interactive=False
    )
    
    # Event handlers
    def start_laptop_wrapper(camera_label):
        """Wrapper to extract camera index from label"""
        if not camera_label:
            return "❌ Error: Please select a camera"
        camera_index = camera_values[camera_labels.index(camera_label)]
        return start_laptop_fn(camera_index)
    
    start_laptop_btn.click(
        fn=start_laptop_wrapper,
        inputs=[camera_dropdown],
        outputs=[camera_status]
    )
    
    start_ip_btn.click(
        fn=start_ip_fn,
        inputs=[rtsp_url],
        outputs=[camera_status]
    )
    
    stop_btn.click(
        fn=stop_fn,
        outputs=[camera_status]
    )
    
    return camera_status
