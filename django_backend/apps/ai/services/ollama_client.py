"""Small local Ollama HTTP client used by Django AI services."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from urllib import error, request

from django.conf import settings


logger = logging.getLogger(__name__)


class OllamaClientError(RuntimeError):
    """Raised when the local Ollama service cannot return a valid response."""


@dataclass(frozen=True)
class OllamaResponse:
    """Normalized response returned by the local Ollama API."""

    answer: str
    model: str
    endpoint: str
    response_time_ms: int = 0


class OllamaClient:
    """Call the local Ollama API with timeout, retry, and safe errors."""

    def __init__(self, host=None, model=None, timeout=None, retries=1, temperature=None, token_limit=None):
        """Configure the local endpoint without using any external AI service."""
        self.host = (host or getattr(settings, "OLLAMA_HOST", "http://localhost:11434")).rstrip("/")
        self.model = model or getattr(settings, "OLLAMA_MODEL", "llama3")
        self.timeout = timeout or getattr(settings, "OLLAMA_TIMEOUT_SECONDS", 30)
        self.retries = max(0, int(retries))
        self.temperature = float(temperature if temperature is not None else getattr(settings, "OLLAMA_TEMPERATURE", 0.2))
        self.token_limit = int(token_limit if token_limit is not None else getattr(settings, "OLLAMA_NUM_PREDICT", 512))

    def _json_request(self, method, path, payload=None):
        """Send one JSON request to Ollama and decode the JSON response."""
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        url = f"{self.host}{path}"
        req = request.Request(url, data=body, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                raw_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            raise OllamaClientError(f"Ollama API returned HTTP {exc.code}.") from exc
        except (error.URLError, TimeoutError, OSError) as exc:
            raise OllamaClientError("Ollama local API is not available.") from exc

        try:
            return json.loads(raw_body or "{}")
        except json.JSONDecodeError as exc:
            raise OllamaClientError("Ollama API returned invalid JSON.") from exc

    def health_check(self):
        """Return local Ollama availability and installed model names."""
        data = self._json_request("GET", "/api/tags")
        models = [item.get("name", "") for item in data.get("models", []) if item.get("name")]
        model_available = any(name == self.model or name.split(":", 1)[0] == self.model for name in models)
        return {
            "available": True,
            "host": self.host,
            "selected_model": self.model,
            "models": models,
            "model_available": model_available,
        }

    def generate_response(self, prompt, options=None, response_format=None):
        """Generate one non-streaming answer from the configured local model."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": options or {
                "temperature": self.temperature,
                "num_predict": self.token_limit,
            },
        }
        if response_format:
            payload["format"] = response_format
        attempts = self.retries + 1
        last_error = None
        for attempt in range(attempts):
            try:
                started = time.perf_counter()
                data = self._json_request("POST", "/api/generate", payload)
                response_time_ms = int((time.perf_counter() - started) * 1000)
                answer = str(data.get("response", "")).strip()
                if not answer:
                    raise OllamaClientError("Ollama response is empty.")
                return OllamaResponse(
                    answer=answer,
                    model=self.model,
                    endpoint=self.host,
                    response_time_ms=response_time_ms,
                )
            except OllamaClientError as exc:
                last_error = exc
                if attempt < attempts - 1:
                    time.sleep(0.1 * (attempt + 1))

        logger.warning("Ollama request failed without logging prompt content: %s", last_error)
        raise last_error or OllamaClientError("Ollama request failed.")
