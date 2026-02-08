from flask import Blueprint, request, jsonify, current_app
from app.models.video_processor import video_processor
from app.utils.camera_handler import camera_handler
import time
import logging

logger = logging.getLogger(__name__)
llm_bp = Blueprint("llm", __name__)


@llm_bp.route("/process", methods=["POST"])
def process_frame():
    """
    Process current frame with LLM

    Request body:
    {
        "task": "describe" | "read" | "summarize" | "custom",
        "provider": "local" | "openai" | "claude" | "ollama" (optional),
        "custom_prompt": "your prompt" (optional, for custom task),
        "model": "gemma3:4b" | "gemma3:12b" | "gemma3:27b" (optional, for Ollama),
        "num_predict": 2600 (optional, for Ollama),
        "temperature": 0.7 (optional, for Ollama)
    }
    """
    try:
        data = request.get_json()
        task = data.get("task", "describe")
        provider = data.get("provider")
        custom_prompt = data.get("custom_prompt")

        # Ollama-specific parameters
        model = data.get("model")
        num_predict = data.get("num_predict")
        temperature = data.get("temperature")

        logger.info(
            f"Processing frame - Task: {task}, Provider: {provider or 'default'}"
        )

        frame = camera_handler.get_current_frame()

        if frame is None:
            logger.warning("Frame processing requested but no frame available")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "No frame available. Please start camera first.",
                    }
                ),
                400,
            )

        start_time = time.time()
        result = video_processor.process_frame(
            frame,
            task=task,
            provider=provider,
            custom_prompt=custom_prompt,
            model=model,
            num_predict=num_predict,
            temperature=temperature,
        )
        elapsed = time.time() - start_time

        if result["success"]:
            logger.info(
                f"Frame processed in {elapsed:.2f}s using {result.get('provider', 'unknown')}"
            )
        else:
            logger.error(f"Frame processing failed: {result.get('error', 'unknown')}")

        return jsonify(result), 200 if result["success"] else 500

    except Exception as e:
        logger.error(f"Exception during frame processing: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@llm_bp.route("/providers", methods=["GET"])
def get_providers():
    """Get available LLM providers and their status"""
    from flask import current_app
    from app.models.ollama_client import ollama_client
    from app.api.settings import get_api_key

    # Check if API keys are available (from settings or config)
    openai_configured = bool(
        get_api_key("openai") or current_app.config.get("OPENAI_API_KEY")
    )
    claude_configured = bool(
        get_api_key("claude") or current_app.config.get("CLAUDE_API_KEY")
    )

    providers = {
        "local": {
            "available": True,
            "model": current_app.config["LOCAL_MODEL_NAME"],
            "device": current_app.config["LOCAL_MODEL_DEVICE"],
        },
        "openai": {
            "available": True,  # Always show, user can configure API key in UI
            "configured": openai_configured,
            "model": current_app.config["OPENAI_MODEL"],
        },
        "claude": {
            "available": True,  # Always show, user can configure API key in UI
            "configured": claude_configured,
            "model": current_app.config["CLAUDE_MODEL"],
        },
        "ollama": {
            "available": True,  # Ollama is always available if configured
            "base_url": current_app.config.get(
                "OLLAMA_BASE_URL", "https://ai.integriert-studieren.jku.at"
            ),
            "default_model": current_app.config.get(
                "OLLAMA_DEFAULT_MODEL", "gemma3:4b"
            ),
            "available_models": ollama_client.get_available_models(),
            "num_predict": current_app.config.get("OLLAMA_NUM_PREDICT", 2600),
            "temperature": current_app.config.get("OLLAMA_TEMPERATURE", 0.7),
        },
    }

    return (
        jsonify(
            {
                "providers": providers,
                "default": current_app.config["DEFAULT_LLM_PROVIDER"],
            }
        ),
        200,
    )


@llm_bp.route("/tasks", methods=["GET"])
def get_tasks():
    """Get available processing tasks"""
    tasks = {
        "read": {
            "name": "Read Text",
            "description": "Read all visible text on the slide or board",
            "prompt": "Read all the text visible on this slide or board clearly and accurately. Include all text content."
        },
        "describe": {
            "name": "Describe",
            "description": "Describe the main content and diagrams",
            "prompt": "Describe what you see on this slide or board, focusing on the main content and any diagrams."
        },
        "summarize": {
            "name": "Summarize",
            "description": "Summarize key points in 2-3 bullet points",
            "prompt": "Summarize the key points shown on this slide or board in 2-3 concise bullet points."
        },
        "custom": {
            "name": "Custom",
            "description": "Use your own prompt",
            "prompt": None
        }
    }

    return jsonify({
        "success": True,
        "tasks": tasks
    }), 200
