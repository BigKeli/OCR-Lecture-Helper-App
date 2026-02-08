import cv2
import numpy as np
import base64
from PIL import Image
import io
from flask import current_app
from app.models.ollama_client import ollama_client


class VideoProcessor:
    """Processes video frames using various LLM providers"""

    def __init__(self):
        self.local_model = None
        self.local_processor = None

    def _load_local_model(self):
        """Lazy load local model"""
        if self.local_model is None:
            try:
                from transformers import BlipProcessor, BlipForConditionalGeneration

                model_name = current_app.config['LOCAL_MODEL_NAME']
                device = current_app.config['LOCAL_MODEL_DEVICE']

                print(f"Loading local model: {model_name} on {device}")
                self.local_processor = BlipProcessor.from_pretrained(model_name)
                self.local_model = BlipForConditionalGeneration.from_pretrained(model_name).to(device)
                print("Local model loaded successfully")
            except Exception as e:
                print(f"Error loading local model: {e}")
                raise

    def _frame_to_pil(self, frame):
        """Convert OpenCV frame to PIL Image"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame_rgb)

    def _frame_to_base64(self, frame):
        """Convert OpenCV frame to base64 string"""
        # Ensure frame is uint8
        if frame.dtype != np.uint8:
            frame = frame.astype(np.uint8)

        # Use OpenCV to encode directly to JPEG (more reliable)
        success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            raise ValueError("Failed to encode frame as JPEG")

        return base64.b64encode(buffer.tobytes()).decode()

    def process_with_local_model(self, frame, task="describe"):
        """Process frame with local model (BLIP)"""
        try:
            self._load_local_model()

            pil_image = self._frame_to_pil(frame)

            if task == "describe":
                inputs = self.local_processor(pil_image, return_tensors="pt").to(
                    current_app.config['LOCAL_MODEL_DEVICE']
                )
                out = self.local_model.generate(**inputs, max_length=50)
                description = self.local_processor.decode(out[0], skip_special_tokens=True)
                return {
                    'success': True,
                    'text': description,
                    'provider': 'local'
                }
            elif task == "read":
                # For reading text, BLIP can generate conditional text
                text = "text on the slide:"
                inputs = self.local_processor(pil_image, text, return_tensors="pt").to(
                    current_app.config['LOCAL_MODEL_DEVICE']
                )
                out = self.local_model.generate(**inputs, max_length=100)
                result = self.local_processor.decode(out[0], skip_special_tokens=True)
                return {
                    'success': True,
                    'text': result,
                    'provider': 'local'
                }
            else:
                return {
                    'success': False,
                    'error': f'Unknown task: {task}',
                    'provider': 'local'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'provider': 'local'
            }

    def process_with_openai(self, frame, prompt):
        """Process frame with OpenAI GPT-4 Vision"""
        try:
            import openai
            from app.api.settings import get_api_key

            # Try to get API key from settings first, then fall back to config
            api_key = get_api_key('openai') or current_app.config.get('OPENAI_API_KEY')
            if not api_key:
                return {
                    'success': False,
                    'error': 'OpenAI API key not configured. Please set it in Settings.',
                    'provider': 'openai'
                }

            client = openai.OpenAI(api_key=api_key)
            base64_image = self._frame_to_base64(frame)

            response = client.chat.completions.create(
                model=current_app.config['OPENAI_MODEL'],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            return {
                'success': True,
                'text': response.choices[0].message.content,
                'provider': 'openai',
                'model': current_app.config['OPENAI_MODEL']
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'provider': 'openai'
            }

    def process_with_claude(self, frame, prompt):
        """Process frame with Claude"""
        try:
            import anthropic
            from app.api.settings import get_api_key

            # Try to get API key from settings first, then fall back to config
            api_key = get_api_key('claude') or current_app.config.get('CLAUDE_API_KEY')
            if not api_key:
                return {
                    'success': False,
                    'error': 'Claude API key not configured. Please set it in Settings.',
                    'provider': 'claude'
                }

            client = anthropic.Anthropic(api_key=api_key)
            base64_image = self._frame_to_base64(frame)

            message = client.messages.create(
                model=current_app.config['CLAUDE_MODEL'],
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": base64_image,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )

            return {
                'success': True,
                'text': message.content[0].text,
                'provider': 'claude',
                'model': current_app.config['CLAUDE_MODEL']
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'provider': 'claude'
            }

    def process_with_ollama(self, frame, prompt, model=None, num_predict=None, temperature=None):
        """Process frame with Ollama Vision API"""
        try:
            # Get config values or use defaults
            if model is None:
                model = current_app.config.get('OLLAMA_DEFAULT_MODEL', 'gemma3:4b')
            if num_predict is None:
                num_predict = current_app.config.get('OLLAMA_NUM_PREDICT', 2600)
            if temperature is None:
                temperature = current_app.config.get('OLLAMA_TEMPERATURE', 0.7)

            # Call Ollama client
            result = ollama_client.generate_vision(
                frame=frame,
                prompt=prompt,
                model=model,
                num_predict=num_predict,
                temperature=temperature,
                stream=False
            )

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'provider': 'ollama'
            }

    def process_frame(self, frame, task="describe", provider=None, custom_prompt=None, model=None, num_predict=None, temperature=None):
        """
        Process a frame with specified provider and task

        Args:
            frame: OpenCV frame (numpy array)
            task: 'describe', 'read', 'summarize', or 'custom'
            provider: 'local', 'openai', 'claude', or 'ollama' (uses default if None)
            custom_prompt: Custom prompt for API providers
            model: Model name (for Ollama: gemma3:4b, gemma3:12b, gemma3:27b)
            num_predict: Maximum tokens to predict (for Ollama)
            temperature: Sampling temperature (for Ollama)

        Returns:
            dict with success, text, provider, and optionally error
        """
        if provider is None:
            provider = current_app.config['DEFAULT_LLM_PROVIDER']

        # Build prompt for API providers
        if provider in ['openai', 'claude', 'ollama']:
            if custom_prompt:
                prompt = custom_prompt
            elif task == "read":
                prompt = "Read all the text visible on this slide or board clearly and accurately. Include all text content."
            elif task == "summarize":
                prompt = "Summarize the key points shown on this slide or board in 2-3 concise bullet points."
            elif task == "describe":
                prompt = "Describe what you see on this slide or board, focusing on the main content and any diagrams."
            else:
                prompt = custom_prompt or "Describe this image."

        # Process based on provider
        if provider == 'local':
            return self.process_with_local_model(frame, task)
        elif provider == 'openai':
            return self.process_with_openai(frame, prompt)
        elif provider == 'claude':
            return self.process_with_claude(frame, prompt)
        elif provider == 'ollama':
            return self.process_with_ollama(frame, prompt, model=model, num_predict=num_predict, temperature=temperature)
        else:
            return {
                'success': False,
                'error': f'Unknown provider: {provider}'
            }


# Global video processor instance
video_processor = VideoProcessor()
