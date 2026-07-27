"""Generate an AI-assisted phase review report with Ollama.

The reviewer is advisory only. It never approves production and it exits
successfully when Ollama is unavailable by generating a warning report.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VALIDATION = PROJECT_ROOT / "docs" / "ai-devops" / "phase_validation_result.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "docs" / "ai-devops" / "AI_PHASE_REVIEW_REPORT.md"
DEFAULT_PROMPT = PROJECT_ROOT / "docs" / "codex-prompts" / "PHASE_12.4_AI_DEVOPS_CONTROL_CENTER.md"
DEFAULT_TEST_PROMPT = PROJECT_ROOT / "docs" / "ai-devops" / "OLLAMA_TEST_PROMPT.md"
DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


def utc_now():
    """Return a timestamp for AI review evidence."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_file(path, limit=8000):
    """Read a text file with a maximum size for prompt safety."""
    target = Path(path)
    if not target.exists():
        return ""
    return target.read_text(encoding="utf-8", errors="replace")[:limit]


def run_git(args):
    """Run a read-only Git command for review context."""
    completed = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def load_validation(path):
    """Load validator JSON if available."""
    target = Path(path)
    if not target.exists():
        return {"status": "MISSING", "missing": ["phase_validation_result.json"], "warnings": []}
    return json.loads(target.read_text(encoding="utf-8"))


def normalize_model_name(name):
    """Normalize Ollama model names so `llama3.1` matches `llama3.1:latest`."""
    return str(name or "").split(":", 1)[0].strip()


def http_json(url, method="GET", payload=None, timeout=5):
    """Call a local Ollama JSON endpoint and return structured output."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return {"ok": True, "status_code": response.status, "data": json.loads(body) if body else {}, "error": ""}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status_code": exc.code, "data": {}, "error": f"HTTP Error {exc.code}: {exc.reason}"}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {"ok": False, "status_code": None, "data": {}, "error": str(exc)}


def list_ollama_models(ollama_url=DEFAULT_OLLAMA_URL, timeout=5):
    """Return installed Ollama models from `/api/tags`."""
    endpoint = ollama_url.rstrip("/") + "/api/tags"
    result = http_json(endpoint, timeout=timeout)
    models = []
    if result["ok"]:
        for item in result["data"].get("models", []):
            name = item.get("name") or item.get("model")
            if name:
                models.append(name)
    return {
        "available": result["ok"],
        "endpoint": endpoint,
        "models": models,
        "error": result["error"],
        "status_code": result["status_code"],
    }


def is_model_available(model, models):
    """Check model by exact name or base name without tag."""
    selected = normalize_model_name(model)
    return any(name == model or normalize_model_name(name) == selected for name in models)


def build_review_prompt(phase, validation, test_result, prompt_file=None):
    """Build the local AI review prompt."""
    selected_prompt = Path(prompt_file) if prompt_file else (DEFAULT_TEST_PROMPT if str(phase) == "12.4.1" else DEFAULT_PROMPT)
    prompt_text = read_file(selected_prompt, limit=3000)
    validation_for_ai = dict(validation)
    if str(phase) == "12.4.1":
        validation_for_ai["notes"] = []
    changed_files = run_git(["diff", "--name-only", "HEAD"])
    staged_files = run_git(["diff", "--cached", "--name-only"])
    latest_commit = run_git(["log", "-1", "--oneline"])

    return f"""
You are an AI phase reviewer for the mecprecision-vietnam migration.

Rules:
- Never approve production.
- Never deploy anything.
- Human architecture approval is required.
- Detect missing documentation, missing tests, security risks, and rollback gaps.

Phase: {phase}
Latest commit: {latest_commit}
Changed files:
{changed_files or staged_files or "No uncommitted changed files detected."}

Validation result:
{json.dumps(validation_for_ai, indent=2, ensure_ascii=False)}

Test result:
{test_result}

Phase 12.4.1 instruction:
This run validates local Ollama connectivity and response handling. Do not
block only because the final Git tag is created after phase finalization.

Phase requirement:
{prompt_text}

Return a concise review with:
1. decision: PASS, PASS_WITH_WARNING, or BLOCKED
2. key risks
3. missing items
4. production safety confirmation
5. human review reminder
""".strip()


def ask_ollama(prompt, model=DEFAULT_MODEL, ollama_url=DEFAULT_OLLAMA_URL, timeout=60):
    """Call Ollama local API and return response text or an error."""
    endpoint = ollama_url.rstrip("/") + "/api/generate"
    model_result = list_ollama_models(ollama_url=ollama_url, timeout=timeout)
    if not model_result["available"]:
        return {
            "available": False,
            "model_available": False,
            "endpoint": endpoint,
            "model": model,
            "models": [],
            "response": "",
            "error": model_result["error"] or "Ollama service is unavailable.",
        }

    if not is_model_available(model, model_result["models"]):
        return {
            "available": False,
            "model_available": False,
            "endpoint": endpoint,
            "model": model,
            "models": model_result["models"],
            "response": "",
            "error": f"Selected model is not installed: {model}",
        }

    result = http_json(
        endpoint,
        method="POST",
        payload={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 220,
                "temperature": 0.1,
            },
        },
        timeout=timeout,
    )
    return {
        "available": result["ok"],
        "model_available": True,
        "endpoint": endpoint,
        "model": model,
        "models": model_result["models"],
        "response": result["data"].get("response", "").strip() if result["ok"] else "",
        "error": result["error"],
        "status_code": result["status_code"],
    }


def parse_ai_decision(text):
    """Extract the first known review decision from AI response text."""
    normalized = str(text or "").upper()
    if "BLOCKED" in normalized:
        return "BLOCKED"
    if "PASS_WITH_WARNING" in normalized:
        return "PASS_WITH_WARNING"
    if "PASS" in normalized:
        return "PASS"
    return "PASS_WITH_WARNING"


def decide(validation, ollama_result):
    """Choose an advisory decision from validation and Ollama state."""
    if validation.get("status") != "PASS":
        return "BLOCKED"
    if not ollama_result.get("available"):
        return "PASS_WITH_WARNING"
    ai_decision = parse_ai_decision(ollama_result.get("response"))
    if ai_decision == "BLOCKED":
        return "BLOCKED"
    if validation.get("warnings") and ai_decision == "PASS":
        return "PASS_WITH_WARNING"
    return ai_decision


def render_report(phase, validation, ollama_result, decision, ollama_url=DEFAULT_OLLAMA_URL, model=DEFAULT_MODEL):
    """Render the AI phase review report as Markdown."""
    ai_text = ollama_result.get("response") or "Ollama is not available. Local validation passed, but AI review is limited."
    return f"""# AI Phase Review Report

## Phase

{phase}

## Created At

{utc_now()}

## Decision

{decision}

## Ollama Integration

- URL: {ollama_url}
- Generate endpoint: {ollama_result.get("endpoint") or ollama_url.rstrip("/") + "/api/generate"}
- Model: {model}
- Available: {ollama_result.get("available")}
- Model available: {ollama_result.get("model_available")}
- Installed models: {ollama_result.get("models", [])}
- Error: {ollama_result.get("error") or "None"}

## Validator Status

- Status: {validation.get("status")}
- Missing: {validation.get("missing", [])}
- Warnings: {validation.get("warnings", [])}
- Notes: {validation.get("notes", [])}

## AI Review

{ai_text}

## Production Safety

- Auto deploy: false
- Auto approve production: false
- Human review required: true

## Final Note

This report is advisory. It does not replace architecture review and does not
authorize production deployment.
"""


def generate_review(
    phase="12.4.1",
    validation_path=None,
    output_path=None,
    test_result="Not provided",
    ollama_url=DEFAULT_OLLAMA_URL,
    model=DEFAULT_MODEL,
    timeout=60,
    prompt_file=None,
):
    """Generate the AI-assisted review report."""
    validation = load_validation(validation_path or DEFAULT_VALIDATION)
    prompt = build_review_prompt(phase, validation, test_result, prompt_file=prompt_file)
    ollama_result = ask_ollama(prompt, model=model, ollama_url=ollama_url, timeout=timeout)
    decision = decide(validation, ollama_result)
    report = render_report(phase, validation, ollama_result, decision, ollama_url=ollama_url, model=model)

    output = Path(output_path or DEFAULT_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    return {
        "phase": phase,
        "decision": decision,
        "ollama_available": ollama_result.get("available"),
        "model": model,
        "model_available": ollama_result.get("model_available"),
        "installed_models": ollama_result.get("models", []),
        "output": str(output),
        "auto_deploy": False,
        "auto_approve_production": False,
        "human_review_required": True,
    }


def main():
    """Command-line entrypoint."""
    parser = argparse.ArgumentParser(description="Generate an Ollama-assisted phase review report.")
    parser.add_argument("--phase", default="12.4.1")
    parser.add_argument("--validation", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--test-result", default="Manual test result not supplied to reviewer script.")
    parser.add_argument("--url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--prompt-file", default=None)
    args = parser.parse_args()

    result = generate_review(
        phase=args.phase,
        validation_path=args.validation,
        output_path=args.output,
        test_result=args.test_result,
        ollama_url=args.url,
        model=args.model,
        timeout=args.timeout,
        prompt_file=args.prompt_file,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
