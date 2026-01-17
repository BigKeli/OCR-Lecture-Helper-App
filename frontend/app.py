import gradio as gr
import requests
import cv2
import numpy as np
from PIL import Image
import time
import os
import socket
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Backend API URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")


class AssistiveClassroomUI:
    def __init__(self):
        self.current_provider = "local"
        self.camera_active = False
        self.stream_url = f"{BACKEND_URL}/api/camera/stream"

        # Get phone URL with actual IP instead of localhost
        self.phone_url = self._get_phone_url()

    def _get_phone_url(self):
        """Get phone camera URL with network IP instead of localhost"""
        # Parse BACKEND_URL to extract components
        from urllib.parse import urlparse

        parsed = urlparse(BACKEND_URL)

        # If backend is localhost, try to get actual local IP
        hostname = parsed.hostname
        if hostname in ["localhost", "127.0.0.1"]:
            local_ip = get_local_ip()
            return f"{parsed.scheme}://{local_ip}:{parsed.port}/phone"
        else:
            return f"{BACKEND_URL}/phone"

    def check_backend_health(self):
        """Check if backend is accessible"""
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=2)
            return response.status_code == 200
        except:
            return False

    def get_available_providers(self):
        """Get available LLM providers from backend"""
        try:
            response = requests.get(f"{BACKEND_URL}/api/llm/providers")
            if response.status_code == 200:
                data = response.json()
                providers = []
                for name, info in data["providers"].items():
                    if info["available"]:
                        providers.append(f"{name} ({info['model']})")
                return (
                    providers
                    if providers
                    else ["local (Salesforce/blip-image-captioning-base)"]
                )
        except:
            pass
        return ["local (Salesforce/blip-image-captioning-base)"]

    def start_laptop_camera(self, camera_index):
        """Start laptop camera"""
        try:
            logger.info(f"Starting laptop camera {camera_index}")
            response = requests.post(
                f"{BACKEND_URL}/api/camera/start/laptop",
                json={"camera_index": int(camera_index)},
            )

            if response.status_code == 200:
                self.camera_active = True
                logger.info("Laptop camera started successfully")
                return "✅ Laptop camera started successfully! Video feed should update automatically."
            else:
                error = response.json().get("error", "Unknown error")
                logger.error(f"Failed to start laptop camera: {error}")
                return f"❌ Error: {error}"

        except Exception as e:
            logger.error(f"Exception starting laptop camera: {e}")
            return f"❌ Error: {str(e)}"

    def start_ip_camera(self, rtsp_url):
        """Start IP camera"""
        try:
            if not rtsp_url:
                return "❌ Error: Please enter RTSP URL"

            logger.info(f"Starting IP camera: {rtsp_url}")
            response = requests.post(
                f"{BACKEND_URL}/api/camera/start/ip", json={"rtsp_url": rtsp_url}
            )

            if response.status_code == 200:
                self.camera_active = True
                logger.info("IP camera started successfully")
                return "✅ IP camera started successfully! Video feed should update automatically."
            else:
                error = response.json().get("error", "Unknown error")
                logger.error(f"Failed to start IP camera: {error}")
                return f"❌ Error: {error}"

        except Exception as e:
            logger.error(f"Exception starting IP camera: {e}")
            return f"❌ Error: {str(e)}"

    def stop_camera(self):
        """Stop camera"""
        try:
            logger.info("Stopping camera")
            response = requests.post(f"{BACKEND_URL}/api/camera/stop")

            if response.status_code == 200:
                self.camera_active = False
                logger.info("Camera stopped successfully")
                return "✅ Camera stopped"
            else:
                error = response.json().get("error", "Unknown error")
                logger.error(f"Failed to stop camera: {error}")
                return f"❌ Error: {error}"

        except Exception as e:
            logger.error(f"Exception stopping camera: {e}")
            return f"❌ Error: {str(e)}"

    def get_video_frame(self):
        """Get current video frame from backend stream"""
        try:
            response = requests.get(self.stream_url, stream=True, timeout=5)

            if response.status_code == 200:
                # Read the first frame from MJPEG stream
                bytes_data = b""
                for chunk in response.iter_content(chunk_size=1024):
                    bytes_data += chunk
                    # Look for JPEG boundaries
                    a = bytes_data.find(b"\xff\xd8")  # JPEG start
                    b = bytes_data.find(b"\xff\xd9")  # JPEG end

                    if a != -1 and b != -1:
                        jpg = bytes_data[a : b + 2]
                        bytes_data = bytes_data[b + 2 :]

                        # Decode image
                        img_array = np.frombuffer(jpg, dtype=np.uint8)
                        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        return Image.fromarray(img)

        except Exception as e:
            print(f"Error getting frame: {e}")

        return None

    def process_frame(self, task, provider_str):
        """Process current frame with LLM"""
        try:
            # Extract provider name from dropdown selection
            provider = provider_str.split(" (")[0]

            logger.info(f"Processing frame with task='{task}', provider='{provider}'")

            response = requests.post(
                f"{BACKEND_URL}/api/llm/process",
                json={"task": task.lower(), "provider": provider},
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    provider_info = result.get("provider", "unknown")
                    model_info = result.get("model", "")
                    text = result["text"]
                    logger.info(f"Frame processed successfully using {provider_info}")
                    return f"**Provider:** {provider_info} {model_info}\n\n**Result:**\n\n{text}"
                else:
                    error_msg = result.get("error", "Unknown error")
                    logger.error(f"Frame processing failed: {error_msg}")
                    return f"❌ Error: {error_msg}"
            else:
                error = response.json().get("error", "Unknown error")
                logger.error(f"HTTP {response.status_code}: {error}")
                return f"❌ Error: {error}"

        except Exception as e:
            logger.error(f"Exception during frame processing: {e}")
            return f"❌ Error: {str(e)}"

    def process_with_custom_prompt(self, custom_prompt, provider_str):
        """Process frame with custom prompt"""
        try:
            if not custom_prompt:
                return "Error: Please enter a custom prompt"

            provider = provider_str.split(" (")[0]

            response = requests.post(
                f"{BACKEND_URL}/api/llm/process",
                json={
                    "task": "custom",
                    "provider": provider,
                    "custom_prompt": custom_prompt,
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    provider_info = result.get("provider", "unknown")
                    model_info = result.get("model", "")
                    text = result["text"]
                    return f"**Provider:** {provider_info} {model_info}\n\n**Result:**\n\n{text}"
                else:
                    return f"Error: {result.get('error', 'Unknown error')}"
            else:
                error = response.json().get("error", "Unknown error")
                return f"Error: {error}"

        except Exception as e:
            return f"Error: {str(e)}"

    def build_interface(self):
        """Build Gradio interface"""

        # Check backend connection
        if not self.check_backend_health():
            logger.warning(f"Backend not accessible at {BACKEND_URL}")
            print(f"⚠️  Warning: Backend not accessible at {BACKEND_URL}")
        else:
            logger.info(f"Backend is accessible at {BACKEND_URL}")

        with gr.Blocks(title="Assistive Classroom") as interface:
            gr.Markdown("# 📹 Assistive Classroom - AI Camera Assistant")
            gr.Markdown(
                "AI-powered camera system to help students with vision/hearing difficulties in classrooms"
            )

            with gr.Row():
                with gr.Column(scale=2):
                    # Video display - Live MJPEG stream
                    video_output = gr.HTML(
                        value=f"""
                        <div style="border: 2px solid #ccc; border-radius: 8px; padding: 10px; background: #000;">
                            <h4 style="color: white; margin: 0 0 10px 0;">Camera Feed</h4>
                            <img id="video-stream" src="{BACKEND_URL}/api/camera/stream"
                                 style="width: 100%; border-radius: 4px; display: block;"
                                 onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22640%22 height=%22480%22><rect fill=%22%23222%22 width=%22640%22 height=%22480%22/><text x=%2250%%22 y=%2250%%22 fill=%22white%22 text-anchor=%22middle%22>No Camera Active</text></svg>'" />
                        </div>
                        """,
                        label="Video Feed",
                    )

                    # Camera controls
                    with gr.Accordion("Camera Settings", open=True):
                        with gr.Tab("Laptop Camera"):
                            camera_index = gr.Number(
                                value=0, label="Camera Index", precision=0
                            )
                            start_laptop_btn = gr.Button(
                                "Start Laptop Camera", variant="primary"
                            )

                        with gr.Tab("IP Camera"):
                            rtsp_url = gr.Textbox(
                                label="RTSP URL",
                                placeholder="rtsp://username:password@ip:port/stream",
                                lines=1,
                            )
                            start_ip_btn = gr.Button(
                                "Start IP Camera", variant="primary"
                            )

                        with gr.Tab("Phone Camera"):
                            gr.Markdown(
                                f"Open this URL on your phone: **{self.phone_url}**"
                            )
                            gr.Markdown(
                                "⚠️ **HTTPS Required**: Most browsers require HTTPS for camera access. Use laptop camera for testing or set up HTTPS."
                            )

                        stop_btn = gr.Button("Stop Camera", variant="stop")

                    camera_status = gr.Textbox(
                        label="Status", value="No camera active", interactive=False
                    )

                with gr.Column(scale=1):
                    # LLM controls
                    gr.Markdown("### AI Processing")

                    provider_dropdown = gr.Dropdown(
                        choices=self.get_available_providers(),
                        value=self.get_available_providers()[0],
                        label="LLM Provider",
                        interactive=True,
                    )

                    gr.Markdown("#### Quick Actions")

                    with gr.Row():
                        read_btn = gr.Button("📖 Read Text", size="sm")
                        describe_btn = gr.Button("🔍 Describe", size="sm")

                    summarize_btn = gr.Button("📝 Summarize", size="sm")

                    # gr.Markdown("#### Custom Prompt")
                    # custom_prompt = gr.Textbox(
                    #     label="Custom Prompt",
                    #     placeholder="Ask anything about the image...",
                    #     lines=3,
                    # )
                    # custom_btn = gr.Button("Send Custom Prompt", variant="secondary")

                    # Output
                    llm_output = gr.Markdown(label="AI Response")

            # Event handlers
            start_laptop_btn.click(
                fn=self.start_laptop_camera,
                inputs=[camera_index],
                outputs=[camera_status],
            )

            start_ip_btn.click(
                fn=self.start_ip_camera, inputs=[rtsp_url], outputs=[camera_status]
            )

            stop_btn.click(fn=self.stop_camera, outputs=[camera_status])

            read_btn.click(
                fn=lambda p: self.process_frame("read", p),
                inputs=[provider_dropdown],
                outputs=[llm_output],
            )

            describe_btn.click(
                fn=lambda p: self.process_frame("describe", p),
                inputs=[provider_dropdown],
                outputs=[llm_output],
            )

            summarize_btn.click(
                fn=lambda p: self.process_frame("summarize", p),
                inputs=[provider_dropdown],
                outputs=[llm_output],
            )

            # custom_btn.click(
            #     fn=self.process_with_custom_prompt,
            #     inputs=[custom_prompt, provider_dropdown],
            #     outputs=[llm_output],
            # )

            # Footer
            gr.Markdown("---")
            gr.Markdown(
                "💡 **Tip:** For phone camera, open the backend URL on your phone and grant camera access."
            )

        return interface


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


if __name__ == "__main__":
    # ANSI color codes
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    ui = AssistiveClassroomUI()
    app = ui.build_interface()

    local_ip = get_local_ip()
    frontend_port = 7860
    backend_ok = ui.check_backend_health()

    print(f"\n{BOLD}{CYAN}🎨 ASSISTIVE CLASSROOM - FRONTEND{RESET}")
    print(f"{GREEN}Local:{RESET}   http://localhost:{frontend_port}")
    print(f"{GREEN}Network:{RESET} http://{local_ip}:{frontend_port}")
    print(
        f"\n{YELLOW}Backend:{RESET} {BACKEND_URL} {'✅' if backend_ok else f'{RED}❌ Not Connected{RESET}'}"
    )

    if not backend_ok:
        print(f"{RED}⚠️  Start backend first: cd backend && python run.py{RESET}")

    print()

    logger.info(f"Launching Gradio UI on port {frontend_port}")

    app.launch(
        server_name="0.0.0.0",
        server_port=frontend_port,
        share=False,
        theme=gr.themes.Soft(),
    )
