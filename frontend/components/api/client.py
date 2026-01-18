"""API client for backend communication"""
import requests
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:6969")


class APIClient:
    """Client for backend API calls"""
    
    def __init__(self, base_url=None):
        self.base_url = base_url or BACKEND_URL
        self.timeout = 30
    
    def _get(self, endpoint, timeout=2):
        """Make GET request"""
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                timeout=timeout
            )
            return response
        except Exception as e:
            logger.error(f"GET {endpoint} failed: {e}")
            return None
    
    def _post(self, endpoint, json_data=None, timeout=None):
        """Make POST request"""
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=json_data,
                timeout=timeout or self.timeout
            )
            return response
        except Exception as e:
            logger.error(f"POST {endpoint} failed: {e}")
            return None
    
    def check_health(self):
        """Check if backend is accessible"""
        response = self._get("/health", timeout=2)
        return response is not None and response.status_code == 200
    
    def get_camera_status(self):
        """Get camera status"""
        response = self._get("/api/camera/status", timeout=2)
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def start_laptop_camera(self, camera_index):
        """Start laptop camera"""
        response = self._post(
            "/api/camera/start/laptop",
            json_data={"camera_index": int(camera_index)}
        )
        if response and response.status_code == 200:
            return response.json()
        elif response:
            return response.json()
        return {"success": False, "error": "Connection failed"}
    
    def start_ip_camera(self, rtsp_url):
        """Start IP camera"""
        response = self._post(
            "/api/camera/start/ip",
            json_data={"rtsp_url": rtsp_url}
        )
        if response and response.status_code == 200:
            return response.json()
        elif response:
            return response.json()
        return {"success": False, "error": "Connection failed"}
    
    def stop_camera(self):
        """Stop camera"""
        response = self._post("/api/camera/stop", timeout=5)
        if response and response.status_code == 200:
            return response.json()
        elif response:
            return response.json()
        return {"success": False, "error": "Connection failed"}
    
    def get_llm_providers(self):
        """Get available LLM providers"""
        response = self._get("/api/llm/providers", timeout=5)
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def process_frame(self, task, provider, custom_prompt=None):
        """Process frame with LLM"""
        json_data = {
            "task": task.lower(),
            "provider": provider
        }
        if custom_prompt:
            json_data["custom_prompt"] = custom_prompt
        
        response = self._post(
            "/api/llm/process",
            json_data=json_data
        )
        if response and response.status_code == 200:
            return response.json()
        elif response:
            return response.json()
        return {"success": False, "error": "Connection failed"}
    
    def get_stream_url(self):
        """Get camera stream URL"""
        return f"{self.base_url}/api/camera/stream"
