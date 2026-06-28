from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .config import get_settings
from .logging_config import get_logger

logger = get_logger(__name__)


def ollama_generate_json(prompt: str, model: str | None = None, timeout: int = 180) -> dict[str, Any] | None:
    """Call the local Ollama daemon and parse a JSON object response."""
    if os.getenv("NEURONOTE_DISABLE_OLLAMA") == "1":
        return None

    settings = get_settings()
    selected_model = model or _resolve_model(settings.ollama_model, settings.ollama_host)
    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2, "num_ctx": 8192},
    }
    request = urllib.request.Request(
        f"{settings.ollama_host}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310
            body = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        logger.warning("Ollama is unavailable or returned invalid JSON: %s", exc)
        return None

    raw = str(body.get("response", "")).strip()
    if not raw:
        return None
    try:
        parsed = json.loads(_extract_json(raw))
    except json.JSONDecodeError as exc:
        logger.warning("Ollama response was not valid JSON: %s", exc)
        return None
    return parsed if isinstance(parsed, dict) else None


def ollama_status() -> dict[str, object]:
    settings = get_settings()
    request = urllib.request.Request(f"{settings.ollama_host}/api/tags", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:  # nosec B310
            body = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return {"available": False, "host": settings.ollama_host, "model": settings.ollama_model, "models": []}
    models = [str(item.get("name", "")) for item in body.get("models", []) if isinstance(item, dict)]
    return {"available": True, "host": settings.ollama_host, "model": settings.ollama_model, "models": models}


def _resolve_model(configured_model: str, host: str) -> str:
    request = urllib.request.Request(f"{host}/api/tags", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:  # nosec B310
            body = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return configured_model

    installed = [str(item.get("name", "")) for item in body.get("models", []) if isinstance(item, dict)]
    if configured_model in installed:
        return configured_model
    for name in installed:
        if name.split(":", 1)[0] == configured_model:
            return name
    return installed[0] if installed else configured_model


def _extract_json(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise json.JSONDecodeError("No JSON object found", text, 0)
    return text[start : end + 1]
