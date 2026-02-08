"""
Ollama Vision API Client

This module provides a client for interacting with the Ollama vision API
using curl/requests. Based on the example PowerShell script provided.
"""
import base64
import json
import requests
import logging
from flask import current_app
from PIL import Image
import io
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for Ollama Vision API"""

    def __init__(self):
        self.base_url = None
        self.username = None
        self.password = None
        self.default_model = None
        self._session = None

    def _get_config(self):
        """Get configuration from Flask app config"""
        self.base_url = current_app.config.get('OLLAMA_BASE_URL', 'https://ai.integriert-studieren.jku.at')
        self.username = current_app.config.get('OLLAMA_USERNAME', 'kvat')
        self.password = current_app.config.get('OLLAMA_PASSWORD', 'kvat123pw')
        self.default_model = current_app.config.get('OLLAMA_DEFAULT_MODEL', 'gemma3:4b')

    def _get_session(self):
        """Get or create requests session with authentication"""
        if self._session is None:
            self._get_config()
            self._session = requests.Session()
            # Set up basic auth
            self._session.auth = (self.username, self.password)
            # Set default headers
            self._session.headers.update({
                'Content-Type': 'application/json'
            })
        return self._session

    def _frame_to_base64(self, frame):
        """
        Convert OpenCV frame to base64 string

        Args:
            frame: OpenCV frame (numpy array)

        Returns:
            base64 encoded JPEG string
        """
        # Validate frame
        if frame is None or not isinstance(frame, np.ndarray):
            raise ValueError("Invalid frame: must be a numpy array")

        if len(frame.shape) != 3 or frame.shape[2] != 3:
            raise ValueError(f"Invalid frame shape: {frame.shape}, expected (H, W, 3)")

        # Ensure frame is uint8
        if frame.dtype != np.uint8:
            frame = frame.astype(np.uint8)

        # Use OpenCV to encode directly to JPEG (more reliable)
        success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            raise ValueError("Failed to encode frame as JPEG")

        # Encode to base64
        img_b64 = base64.b64encode(buffer.tobytes()).decode('utf-8')

        logger.debug(f"Frame encoded: shape={frame.shape}, base64_len={len(img_b64)}")
        return img_b64

    def generate_vision(
        self,
        frame,
        prompt,
        model=None,
        num_predict=2600,
        temperature=0.7,
        stream=False
    ):
        """
        Generate vision response from Ollama API
        
        Args:
            frame: OpenCV frame (numpy array) or PIL Image
            prompt: Text prompt for the vision model
            model: Model name (defaults to config)
            num_predict: Maximum number of tokens to predict
            temperature: Sampling temperature (0.0-1.0)
            stream: Whether to stream the response
            
        Returns:
            dict with success, response text, model, and optionally error
        """
        try:
            self._get_config()
            session = self._get_session()
            
            # Use provided model or default
            model_name = model or self.default_model
            
            # Convert frame to base64 if it's a numpy array
            if isinstance(frame, np.ndarray):
                img_b64 = self._frame_to_base64(frame)
            elif isinstance(frame, Image.Image):
                # Convert PIL Image to base64
                buffered = io.BytesIO()
                frame.save(buffered, format="JPEG", quality=85)
                img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            else:
                return {
                    'success': False,
                    'error': 'Invalid frame type. Expected numpy array or PIL Image.'
                }
            
            # Build request payload
            payload = {
                "model": model_name,
                "prompt": prompt,
                "images": [img_b64],
                "stream": stream,
                "options": {
                    "num_predict": num_predict,
                    "temperature": temperature
                }
            }
            
            # Make API request
            api_url = f"{self.base_url}/api/generate"
            logger.info(f"Calling Ollama API: {api_url} with model {model_name}")
            
            response = session.post(
                api_url,
                json=payload,
                timeout=120  # 2 minute timeout for large responses
            )
            
            # Check response status
            response.raise_for_status()
            
            # Parse JSON response
            result = response.json()
            
            # Extract response text
            response_text = result.get('response', '')
            
            logger.info(f"Ollama API call successful. Response length: {len(response_text)}")
            
            return {
                'success': True,
                'text': response_text,
                'provider': 'ollama',
                'model': result.get('model', model_name),
                'num_predict': result.get('num_predict'),
                'total_duration': result.get('total_duration'),
                'load_duration': result.get('load_duration'),
                'prompt_eval_count': result.get('prompt_eval_count'),
                'prompt_eval_duration': result.get('prompt_eval_duration'),
                'eval_count': result.get('eval_count'),
                'eval_duration': result.get('eval_duration')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API request failed: {e}")
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg = error_detail.get('error', error_msg)
                except:
                    error_msg = e.response.text or error_msg
            return {
                'success': False,
                'error': f'Ollama API error: {error_msg}',
                'provider': 'ollama'
            }
        except Exception as e:
            logger.error(f"Unexpected error in Ollama client: {e}")
            return {
                'success': False,
                'error': str(e),
                'provider': 'ollama'
            }

    def get_available_models(self):
        """
        Get list of available models from Ollama
        
        Returns:
            list of available model names
        """
        return ['gemma3:4b', 'gemma3:12b', 'gemma3:27b']


# Global Ollama client instance
ollama_client = OllamaClient()
