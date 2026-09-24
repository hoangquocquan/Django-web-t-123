"""Check local Ollama readiness for AI DevOps review.

This script talks only to the local Ollama endpoint. It does not use external
AI APIs and does not send project source code anywhere.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "ai-devops" / "ollama_environment_check.json"
DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


def utc_now():
    """Return an ISO timestamp for validation evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_model_name(name):
    """Normalize Ollama model names so `llama3.1` matches `llama3.1:latest`."""
    return str(name or "").split(":", 1)[0].strip()


def http_json(url, method="GET", payload=None, timeout=5):
    """Call a local JSON endpoint and return data or a structured error."""
    body = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return {"ok": True, "status_code": response.status, "data": json.loads(raw) if raw else {}, "error": ""}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status_code": exc.code, "data": {}, "error": f"HTTP Error {exc.code}: {exc.reason}"}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "status_code": None, "data": {}, "error": str(exc)}


def extract_models(tags_payload):
    """Extract model names from Ollama `/api/tags` response."""
    models = []
    for item in tags_payload.get("models", []):
        name = item.get("name") or item.get("model")
        if name:
            models.append(name)
    return models


def model_available(selected_model, models):
    """Return true when selected model exists exactly or by base name."""
    selected = normalize_model_name(selected_model)
    return any(name == selected_model or normalize_model_name(name) == selected for name in models)


def check_environment(ollama_url=DEFAULT_OLLAMA_URL, model=DEFAULT_MODEL, output_path=None, timeout=5):
    """Check service availability, installed models, and selected model state."""
    endpoint = ollama_url.rstrip("/")
    tags_url = endpoint + "/api/tags"
    tags_result = http_json(tags_url, timeout=timeout)
    models = extract_models(tags_result["data"]) if tags_result["ok"] else []
    selected_available = model_available(model, models)

    if not tags_result["ok"]:
        status = "OLLAMA_NOT_READY"
    elif not selected_available:
        status = "MODEL_NOT_FOUND"
    else:
        status = "READY"

    result = {
        "phase": "12.4.1",
        "created_at": utc_now(),
        "available": tags_result["ok"] and selected_available,
        "endpoint": endpoint,
        "api_endpoint": tags_url,
        "selected_model": model,
        "selected_model_available": selected_available,
        "models": models,
        "model_count": len(models),
        "api_status_code": tags_result["status_code"],
        "error": tags_result["error"],
        "status": status,
        "safety": {
            "external_ai_used": False,
            "project_code_sent_outside_local_machine": False,
            "auto_approve_production": False,
            "human_review_required": True,
        },
    }

    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main():
    """Command-line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Check local Ollama environment.")
    parser.add_argument("--url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--output", default=None)
    parser.add_argument("--timeout", type=int, default=5)
    args = parser.parse_args()

    result = check_environment(args.url, args.model, args.output, args.timeout)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
