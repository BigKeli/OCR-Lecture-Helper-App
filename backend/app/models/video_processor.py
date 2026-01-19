"""Video processor - delegates to OpenAI handler for image analysis"""
from app.services.openai_handler import openai_handler
import logging

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Processes video frames using OpenAI vision API"""

    def __init__(self):
        self.handler = openai_handler

    def process_frame(self, frame, task: str = "describe", custom_prompt: str = None, system_prompt: str = None) -> dict:
        """
        Process a frame with the specified task.

        Args:
            frame: OpenCV frame (numpy array)
            task: 'describe', 'read', 'summarize', or 'custom'
            custom_prompt: Custom user prompt (required for 'custom' task)
            system_prompt: Optional system prompt to inject

        Returns:
            dict with success, text, model, and optionally error
        """
        logger.info(f"Processing frame with task: {task}")

        if task == "read":
            return self.handler.read_text(frame, custom_system_prompt=system_prompt)
        elif task == "describe":
            return self.handler.describe(frame, custom_system_prompt=system_prompt)
        elif task == "summarize":
            return self.handler.summarize(frame, custom_system_prompt=system_prompt)
        elif task == "custom":
            if not custom_prompt:
                return {'success': False, 'error': 'custom_prompt is required for custom task'}
            return self.handler.custom_query(frame, user_prompt=custom_prompt, system_prompt=system_prompt)
        else:
            return {'success': False, 'error': f'Unknown task: {task}'}


# Global video processor instance
video_processor = VideoProcessor()
