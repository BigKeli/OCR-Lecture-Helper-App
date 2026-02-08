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
        self.current_provider = "local"
        self.camera_active = False
        self.stream_url = f"{BACKEND_URL}/api/camera/stream"

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
                    # Skip local Salesforce model
                    if name == "local":
                        continue

                    # Always show all providers (user can configure API keys in UI)
                    if name == "ollama":
                        model_name = info.get("default_model", "gemma3:4b")
                        # Extract version from model name (e.g., "4b" from "gemma3:4b")
                        version = (
                            model_name.split(":")[-1].upper()
                            if ":" in model_name
                            else "4B"
                        )
                        providers.append(f"JKU Ollama {version} (ollama)")
                    elif name == "openai":
                        model = info.get("model", "gpt-4o")
                        providers.append(f"OpenAI {model} (openai)")
                    elif name == "claude":
                        model = info.get("model", "claude-3-5-sonnet")
                        providers.append(f"Claude {model} (claude)")
                    else:
                        model = info.get("model", "unknown")
                        providers.append(f"{name.capitalize()} ({model})")

                return providers if providers else ["JKU Ollama 4B (ollama)"]
        except Exception as e:
            logger.error(f"Failed to get providers: {e}")
        return ["JKU Ollama 4B (ollama)"]

    def start_camera(self, rtsp_url):
        """Start RTSP camera"""
        try:
            if not rtsp_url:
                return "Please enter RTSP URL"

            logger.info(f"Starting camera: {rtsp_url}")
            response = requests.post(
                f"{BACKEND_URL}/api/camera/start", json={"rtsp_url": rtsp_url}
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

    def get_video_frame(self):
        """Get current video frame from backend /frame endpoint"""
        try:
            response = requests.get(f"{BACKEND_URL}/api/camera/frame", timeout=5)

            if response.status_code == 200:
                img_array = np.frombuffer(response.content, dtype=np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                if img is not None:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    return Image.fromarray(img)

        except Exception as e:
            print(f"Error getting frame: {e}")

        return None

    def process_frame(self, task, provider_str):
        """Process current frame with LLM"""
        try:
            # Extract provider name from dropdown selection (e.g., "OpenAI gpt-4o (openai)" -> "openai")
            if "(ollama)" in provider_str.lower():
                provider = "ollama"
            elif "(openai)" in provider_str.lower():
                provider = "openai"
            elif "(claude)" in provider_str.lower():
                provider = "claude"
            elif " (" in provider_str and ")" in provider_str:
                # Extract from parentheses: "Name (provider)" -> "provider"
                provider = provider_str.split("(")[-1].split(")")[0].strip()
            else:
                provider = provider_str
            logger.info(f"Processing frame with task='{task}', provider='{provider}'")

            response = requests.post(
                f"{BACKEND_URL}/api/llm/process",
                json={"task": task.lower(), "provider": provider},
                timeout=120,  # Increased timeout for Ollama responses
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
                    return f"Error: {error_msg}"
            else:
                error = response.json().get("error", "Unknown error")
                logger.error(f"HTTP {response.status_code}: {error}")
                return f"Error: {error}"

        except Exception as e:
            logger.error(f"Exception during frame processing: {e}")
            return f"Error: {str(e)}"

    def process_with_custom_prompt(self, custom_prompt, provider_str):
        """Process frame with custom prompt"""
        try:
            if not custom_prompt:
                return "❌ Error: Please enter a custom prompt"

            # Extract provider name from dropdown selection
            if "(ollama)" in provider_str.lower():
                provider = "ollama"
            elif "(openai)" in provider_str.lower():
                provider = "openai"
            elif "(claude)" in provider_str.lower():
                provider = "claude"
            elif " (" in provider_str and ")" in provider_str:
                provider = provider_str.split("(")[-1].split(")")[0].strip()
            else:
                provider = provider_str

            response = requests.post(
                f"{BACKEND_URL}/api/llm/process",
                json={
                    "task": "custom",
                    "provider": provider,
                    "custom_prompt": custom_prompt,
                },
                timeout=120,  # Increased timeout for Ollama responses
            )

            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    provider_info = result.get("provider", "unknown")
                    model_info = result.get("model", "")
                    text = result["text"]
                    return f"**Provider:** {provider_info} {model_info}\n\n**Result:**\n\n{text}"
                else:
                    return f"❌ Error: {result.get('error', 'Unknown error')}"
            else:
                error = response.json().get("error", "Unknown error")
                return f"❌ Error: {error}"

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def process_detailed_analysis(self, provider_str):
        """Process frame with detailed analysis (2000 words)"""
        detailed_prompt = "Describe this image in great detail with approximately 2000 words. Include all visible text, objects, people, colors, composition, context, and any other relevant information you can observe."
        return self.process_with_custom_prompt(detailed_prompt, provider_str)

    def update_single_api_key(self, provider, api_key):
        """Update a single API key"""
        try:
            payload = {}
            if provider == "openai":
                payload["openai_api_key"] = api_key
            elif provider == "claude":
                payload["claude_api_key"] = api_key

            response = requests.post(
                f"{BACKEND_URL}/api/settings/api-keys", json=payload, timeout=5
            )

            if response.status_code == 200:
                result = response.json()
                status = result.get("status", {})
                is_configured = status.get(provider, False)

                if is_configured:
                    return f"✅ {provider.capitalize()} API key saved successfully!"
                else:
                    return f"⚠️ {provider.capitalize()} API key cleared"
            else:
                error = response.json().get("error", "Unknown error")
                return f"❌ Error: {error}"

        except Exception as e:
            logger.error(f"Exception updating {provider} API key: {e}")
            return f"❌ Error: {str(e)}"

    def update_provider_visibility(self, provider_str):
        """Update visibility of API key inputs based on selected provider"""
        # Extract provider name
        if "openai" in provider_str.lower() or "gpt" in provider_str.lower():
            return gr.update(visible=True), gr.update(visible=False)
        elif "claude" in provider_str.lower():
            return gr.update(visible=False), gr.update(visible=True)
        else:
            return gr.update(visible=False), gr.update(visible=False)

    def build_interface(self):
        """Build Gradio interface"""

        if not self.check_backend_health():
            logger.warning(f"Backend not accessible at {BACKEND_URL}")
            print(f"Warning: Backend not accessible at {BACKEND_URL}")
        else:
            logger.info(f"Backend is accessible at {BACKEND_URL}")

        with gr.Blocks(title="Assistive Classroom") as interface:
            gr.Markdown("# Assistive Classroom - AI Camera Assistant")
            gr.Markdown(
                "AI-powered camera system to help students with vision/hearing difficulties in classrooms"
            )

            with gr.Row():
                with gr.Column(scale=2):
                    # Video display using Gradio Image component
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
                            refresh_btn = gr.Button(
                                "Refresh Frame", variant="secondary"
                            )

                    camera_status = gr.Textbox(
                        label="Status", value="No camera active", interactive=False
                    )

                with gr.Column(scale=1):
                    # LLM controls
                    gr.Markdown("### AI Processing")

                    gr.Markdown(
                        "💡 **Tip:** Select **Local JKU Ollama** for powerful vision analysis!"
                    )

                    provider_dropdown = gr.Dropdown(
                        choices=self.get_available_providers(),
                        value=self.get_available_providers()[0],
                        label="LLM Provider",
                        interactive=True,
                    )

                    # API Key inputs (conditional visibility based on provider)
                    with gr.Group(visible=False) as openai_api_group:
                        gr.Markdown("#### OpenAI API Key Required")
                        openai_api_key_input = gr.Textbox(
                            label="OpenAI API Key",
                            placeholder="sk-...",
                            type="password",
                            lines=1,
                        )
                        save_openai_btn = gr.Button("💾 Save OpenAI Key", size="sm")
                        openai_status = gr.Markdown("")

                    with gr.Group(visible=False) as claude_api_group:
                        gr.Markdown("#### Claude API Key Required")
                        claude_api_key_input = gr.Textbox(
                            label="Claude API Key",
                            placeholder="sk-ant-...",
                            type="password",
                            lines=1,
                        )
                        save_claude_btn = gr.Button("💾 Save Claude Key", size="sm")
                        claude_status = gr.Markdown("")

                    gr.Markdown("#### Quick Actions")

                    with gr.Row():
                        read_btn = gr.Button("Read Text", size="sm")
                        describe_btn = gr.Button("Describe", size="sm")

                    with gr.Row():
                        summarize_btn = gr.Button("📝 Summarize", size="sm")
                        detailed_btn = gr.Button(
                            "📝 Detailed Analysis", size="sm", variant="primary"
                        )
                    gr.Markdown("#### Custom Prompt")
                    custom_prompt = gr.Textbox(
                        label="Custom Prompt",
                        placeholder="Ask anything about the image...",
                        lines=3,
                    )
                    custom_btn = gr.Button("Send Custom Prompt", variant="secondary")

                    # Output
                    llm_output = gr.Markdown(label="AI Response")

            # Event handlers
            # Update API key input visibility based on provider selection
            provider_dropdown.change(
                fn=self.update_provider_visibility,
                inputs=[provider_dropdown],
                outputs=[openai_api_group, claude_api_group],
            )
            start_btn.click(
                fn=self.start_camera,
                inputs=[rtsp_url],
                outputs=[camera_status],
            ).then(
                fn=self.get_video_frame,
                outputs=[video_output],
            )

            stop_btn.click(fn=self.stop_camera, outputs=[camera_status])

            refresh_btn.click(
                fn=self.get_video_frame,
                outputs=[video_output],
            )

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

            detailed_btn.click(
                fn=self.process_detailed_analysis,
                inputs=[provider_dropdown],
                outputs=[llm_output],
            )

            custom_btn.click(
                fn=self.process_with_custom_prompt,
                inputs=[custom_prompt, provider_dropdown],
                outputs=[llm_output],
            )

            # API Key save handlers
            save_openai_btn.click(
                fn=lambda key: self.update_single_api_key("openai", key),
                inputs=[openai_api_key_input],
                outputs=[openai_status],
            )

            save_claude_btn.click(
                fn=lambda key: self.update_single_api_key("claude", key),
                inputs=[claude_api_key_input],
                outputs=[claude_status],
            )

            # Footer
            gr.Markdown("---")
            gr.Markdown(
                "💡 **Tip:** For phone camera, open the backend URL on your phone and grant camera access."
            )

        return interface


if __name__ == "__main__":
    ui = AssistiveClassroomUI()
    app = ui.build_interface()

    frontend_port = 7860
    backend_ok = ui.check_backend_health()

    print(f"\nAssistive Classroom - Frontend")
    print(f"Local:   http://localhost:{frontend_port}")
    print(
        f"Backend: {BACKEND_URL} {'(connected)' if backend_ok else '(not connected)'}"
    )

    if not backend_ok:
        print("Start backend first: cd backend && python run.py")

    print()

    logger.info(f"Launching Gradio UI on port {frontend_port}")

    app.launch(
        server_name="0.0.0.0",
        server_port=frontend_port,
        share=False,
        theme=gr.themes.Soft(),
    )
