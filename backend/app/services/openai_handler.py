"""OpenAI API handler for image processing"""

import base64
import io
from PIL import Image
import cv2
import openai
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class OpenAIHandler:
    """Handles all OpenAI API interactions for image analysis"""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            api_key = current_app.config.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            self._client = openai.OpenAI(api_key=api_key)
        return self._client

    @property
    def model(self):
        """Get configured model name"""
        return current_app.config.get("OPENAI_MODEL", "gpt-4o")

    def _frame_to_base64(self, frame) -> str:
        """Convert OpenCV frame (numpy array) to base64 string"""
        import hashlib
        frame_hash = hashlib.md5(frame.tobytes()).hexdigest()[:8]
        print(f"DEBUG: OpenAI encoding frame, hash={frame_hash}", flush=True)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(frame_rgb)

        buffered = io.BytesIO()
        pil_img.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

    def build_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """
        Concatenate system prompt with user prompt.
        Allows injecting custom system prompts.

        Args:
            system_prompt: The system-level instruction
            user_prompt: The user's specific request

        Returns:
            Combined prompt string
        """
        if system_prompt and user_prompt:
            return f"{system_prompt}\n\n{user_prompt}"
        return system_prompt or user_prompt

    def _call_vision_api(self, frame, prompt: str) -> dict:
        """
        Make a vision API call to OpenAI.

        Args:
            frame: OpenCV frame (numpy array)
            prompt: The prompt to send
            max_tokens: Maximum tokens in response

        Returns:
            dict with success, text, model, and optionally error
        """
        try:
            base64_image = self._frame_to_base64(frame)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "low",
                                },
                            },
                        ],
                    }
                ],
            )

            return {
                "success": True,
                "text": response.choices[0].message.content,
                "model": self.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }

        except openai.APIConnectionError as e:
            logger.error(f"OpenAI connection error: {e}")
            return {"success": False, "error": f"Connection error: {str(e)}"}
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit: {e}")
            return {
                "success": False,
                "error": "Rate limit exceeded. Please try again later.",
            }
        except openai.APIStatusError as e:
            logger.error(f"OpenAI API error: {e}")
            return {"success": False, "error": f"API error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"success": False, "error": str(e)}

    def read_text(self, frame, custom_system_prompt: str = None) -> dict:
        """
        Read all text visible in the image.

        Args:
            frame: OpenCV frame
            custom_system_prompt: Optional custom system prompt to prepend

        Returns:
            dict with success, text, model
        """
        system_prompt = (
            custom_system_prompt
            or "You are an OCR assistant that accurately reads text from images."
        )
        user_prompt = "Read all the text visible on this slide or board clearly and accurately. Include all text content, maintaining the original structure and formatting where possible."

        prompt = self.build_prompt(system_prompt, user_prompt)
        logger.info("Processing: read_text")
        return self._call_vision_api(frame, prompt)

    def describe(self, frame, custom_system_prompt: str = None) -> dict:
        """
        Describe the content of the image.

        Args:
            frame: OpenCV frame
            custom_system_prompt: Optional custom system prompt to prepend

        Returns:
            dict with success, text, model
        """
        system_prompt = (
            custom_system_prompt
            or "You are a helpful assistant that describes educational content clearly."
        )
        user_prompt = "Describe the image"
        

        prompt = self.build_prompt(system_prompt, user_prompt)
        logger.info("Processing: describe")
        return self._call_vision_api(frame, prompt)

    def summarize(self, frame, custom_system_prompt: str = None) -> dict:
        """
        Summarize key points from the image.

        Args:
            frame: OpenCV frame
            custom_system_prompt: Optional custom system prompt to prepend

        Returns:
            dict with success, text, model
        """
        system_prompt = (
            custom_system_prompt
            or "You are an assistant that creates clear, concise summaries of educational content."
        )
        user_prompt = "Summarize the key points shown on this slide or board in 2-4 concise bullet points. Focus on the most important information."

        prompt = self.build_prompt(system_prompt, user_prompt)
        logger.info("Processing: summarize")
        return self._call_vision_api(frame, prompt)

    def custom_query(self, frame, user_prompt: str, system_prompt: str = None) -> dict:
        """
        Process image with a custom prompt.

        Args:
            frame: OpenCV frame
            user_prompt: The user's custom prompt
            system_prompt: Optional system prompt

        Returns:
            dict with success, text, model
        """
        system_prompt = (
            system_prompt
            or "You are a helpful assistant analyzing educational content."
        )
        prompt = self.build_prompt(system_prompt, user_prompt)
        logger.info(f"Processing: custom_query")
        return self._call_vision_api(frame, prompt)


# Global instance
openai_handler = OpenAIHandler()
