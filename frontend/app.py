import gradio as gr
import requests
import cv2
import numpy as np
from PIL import Image
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")


class AssistiveClassroomUI:
    def __init__(self):
        self.camera_active = False

    def check_backend_health(self):
        """Check if backend is accessible"""
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=2)
            return response.status_code == 200
        except:
            return False

    def start_camera(self, rtsp_url):
        """Start RTSP camera"""
        try:
            if not rtsp_url:
                return "Please enter RTSP URL"

            logger.info(f"Starting camera: {rtsp_url}")
            response = requests.post(
                f"{BACKEND_URL}/api/camera/start",
                json={"rtsp_url": rtsp_url},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                self.camera_active = True
                logger.info("Camera started successfully")
                return "Camera started successfully"
            else:
                error = response.json().get("error", "Unknown error")
                logger.error(f"Failed to start camera: {error}")
                return f"Error: {error}"

        except Exception as e:
            logger.error(f"Exception starting camera: {e}")
            return f"Error: {str(e)}"

    def stop_camera(self):
        """Stop camera"""
        try:
            logger.info("Stopping camera")
            response = requests.post(f"{BACKEND_URL}/api/camera/stop")

            if response.status_code == 200:
                self.camera_active = False
                logger.info("Camera stopped successfully")
                return "Camera stopped"
            else:
                error = response.json().get("error", "Unknown error")
                logger.error(f"Failed to stop camera: {error}")
                return f"Error: {error}"

        except Exception as e:
            logger.error(f"Exception stopping camera: {e}")
            return f"Error: {str(e)}"

    def capture_and_display_frame(self):
        """Capture a snapshot and display it"""
        try:
            # First, capture the snapshot
            capture_response = requests.post(
                f"{BACKEND_URL}/api/camera/capture",
                headers={"Content-Type": "application/json"},
                timeout=5
            )

            if capture_response.status_code != 200:
                logger.error("Failed to capture snapshot")
                return None

            # Then get the captured frame
            frame_response = requests.get(f"{BACKEND_URL}/api/camera/frame", timeout=5)

            if frame_response.status_code == 200:
                img_array = np.frombuffer(frame_response.content, dtype=np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                if img is not None:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    return Image.fromarray(img)

        except Exception as e:
            logger.error(f"Error capturing frame: {e}")

        return None

    def _format_result(self, result: dict) -> str:
        """Format API result for display"""
        if result["success"]:
            model = result.get("model", "gpt-4o")
            proc_time = result.get("processing_time", "N/A")
            text = result["text"]
            return f"**Model:** {model} | **Time:** {proc_time}s\n\n---\n\n{text}"
        else:
            return f"Error: {result.get('error', 'Unknown error')}"

    def read_text(self) -> str:
        """Read all text from current frame"""
        logger.info("Action: read_text")
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/llm/read",
                headers={"Content-Type": "application/json"},
                json={},
                timeout=60,
            )
            if response.status_code == 200:
                return self._format_result(response.json())
            else:
                return f"Error: {response.json().get('error', 'Unknown error')}"
        except Exception as e:
            logger.error(f"Exception in read_text: {e}")
            return f"Error: {str(e)}"

    def describe(self) -> str:
        """Describe the content of current frame"""
        logger.info("Action: describe")
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/llm/describe",
                headers={"Content-Type": "application/json"},
                json={},
                timeout=60,
            )
            if response.status_code == 200:
                return self._format_result(response.json())
            else:
                return f"Error: {response.json().get('error', 'Unknown error')}"
        except Exception as e:
            logger.error(f"Exception in describe: {e}")
            return f"Error: {str(e)}"

    def summarize(self) -> str:
        """Summarize key points from current frame"""
        logger.info("Action: summarize")
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/llm/summarize",
                headers={"Content-Type": "application/json"},
                json={},
                timeout=60,
            )
            if response.status_code == 200:
                return self._format_result(response.json())
            else:
                return f"Error: {response.json().get('error', 'Unknown error')}"
        except Exception as e:
            logger.error(f"Exception in summarize: {e}")
            return f"Error: {str(e)}"

    def custom_query(self, prompt: str) -> str:
        """Process frame with custom prompt"""
        if not prompt:
            return "Error: Please enter a prompt"

        logger.info("Action: custom_query")
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/llm/custom",
                headers={"Content-Type": "application/json"},
                json={"prompt": prompt},
                timeout=60,
            )
            if response.status_code == 200:
                return self._format_result(response.json())
            else:
                return f"Error: {response.json().get('error', 'Unknown error')}"
        except Exception as e:
            logger.error(f"Exception in custom_query: {e}")
            return f"Error: {str(e)}"

    def build_interface(self):
        """Build Gradio interface"""

        if not self.check_backend_health():
            logger.warning(f"Backend not accessible at {BACKEND_URL}")
            print(f"Warning: Backend not accessible at {BACKEND_URL}")
        else:
            logger.info(f"Backend is accessible at {BACKEND_URL}")

        with gr.Blocks(title="Assistive Classroom", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# Assistive Classroom - AI Camera Assistant")
            gr.Markdown(
                "AI-powered camera system to help students with vision/hearing difficulties in classrooms"
            )

            with gr.Row():
                with gr.Column(scale=2):
                    # Video display
                    video_output = gr.Image(
                        label="Camera Feed",
                        height=480,
                    )

                    # Camera controls
                    with gr.Accordion("Camera Settings", open=True):
                        rtsp_url = gr.Textbox(
                            label="RTSP URL",
                            placeholder="rtsp://username:password@ip:port/stream",
                            lines=1,
                        )
                        with gr.Row():
                            start_btn = gr.Button("Start Camera", variant="primary")
                            stop_btn = gr.Button("Stop Camera", variant="stop")
                            refresh_btn = gr.Button("Refresh Frame", variant="secondary")

                    camera_status = gr.Textbox(
                        label="Status", value="No camera active", interactive=False
                    )

                with gr.Column(scale=1):
                    # LLM controls
                    gr.Markdown("### AI Processing")

                    gr.Markdown("#### Quick Actions")
                    with gr.Row():
                        read_btn = gr.Button("Read Text", variant="primary")
                        describe_btn = gr.Button("Describe", variant="secondary")

                    summarize_btn = gr.Button("Summarize", variant="secondary")

                    gr.Markdown("#### Custom Prompt")
                    custom_prompt = gr.Textbox(
                        label="Custom Prompt",
                        placeholder="Ask anything about the image...",
                        lines=3,
                    )
                    custom_btn = gr.Button("Send Custom Prompt", variant="primary")

                    # Output
                    llm_output = gr.Markdown(label="AI Response")

            # Event handlers
            start_btn.click(
                fn=self.start_camera,
                inputs=[rtsp_url],
                outputs=[camera_status],
            ).then(
                fn=self.capture_and_display_frame,
                outputs=[video_output],
            )

            stop_btn.click(fn=self.stop_camera, outputs=[camera_status])

            refresh_btn.click(
                fn=self.capture_and_display_frame,
                outputs=[video_output],
            )

            read_btn.click(
                fn=self.read_text,
                outputs=[llm_output],
            )

            describe_btn.click(
                fn=self.describe,
                outputs=[llm_output],
            )

            summarize_btn.click(
                fn=self.summarize,
                outputs=[llm_output],
            )

            custom_btn.click(
                fn=self.custom_query,
                inputs=[custom_prompt],
                outputs=[llm_output],
            )

        return interface


if __name__ == "__main__":
    ui = AssistiveClassroomUI()
    app = ui.build_interface()

    frontend_port = 7860
    backend_ok = ui.check_backend_health()

    print(f"\nAssistive Classroom - Frontend")
    print(f"Local:   http://localhost:{frontend_port}")
    print(f"Backend: {BACKEND_URL} {'(connected)' if backend_ok else '(not connected)'}")

    if not backend_ok:
        print("Start backend first: cd backend && python run.py")

    print()

    logger.info(f"Launching Gradio UI on port {frontend_port}")

    app.launch(
        server_name="0.0.0.0",
        server_port=frontend_port,
        share=False,
    )
