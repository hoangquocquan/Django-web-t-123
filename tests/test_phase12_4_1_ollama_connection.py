import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.check_ollama_environment import check_environment, extract_models, model_available
from scripts.ollama_phase_reviewer import ask_ollama, generate_review, parse_ai_decision


def test_ollama_unavailable_handling(monkeypatch, tmp_path):
    def fake_http_json(url, method="GET", payload=None, timeout=5):
        return {"ok": False, "status_code": None, "data": {}, "error": "connection refused"}

    monkeypatch.setattr("scripts.check_ollama_environment.http_json", fake_http_json)
    result = check_environment(output_path=tmp_path / "ollama.json")

    assert result["status"] == "OLLAMA_NOT_READY"
    assert result["available"] is False
    assert result["safety"]["external_ai_used"] is False
    assert result["safety"]["auto_approve_production"] is False


def test_api_connection_and_model_validation(monkeypatch, tmp_path):
    def fake_http_json(url, method="GET", payload=None, timeout=5):
        return {
            "ok": True,
            "status_code": 200,
            "data": {"models": [{"name": "llama3.1:latest"}, {"name": "mistral:latest"}]},
            "error": "",
        }

    monkeypatch.setattr("scripts.check_ollama_environment.http_json", fake_http_json)
    result = check_environment(model="llama3.1", output_path=tmp_path / "ollama.json")

    assert result["status"] == "READY"
    assert result["available"] is True
    assert result["selected_model_available"] is True
    assert "llama3.1:latest" in result["models"]


def test_model_helper_functions():
    payload = {"models": [{"name": "llama3.1:latest"}, {"model": "qwen2.5:7b"}]}
    models = extract_models(payload)

    assert model_available("llama3.1", models)
    assert model_available("qwen2.5:7b", models)
    assert not model_available("missing-model", models)


def test_response_parsing():
    assert parse_ai_decision("decision: BLOCKED") == "BLOCKED"
    assert parse_ai_decision("decision: PASS_WITH_WARNING") == "PASS_WITH_WARNING"
    assert parse_ai_decision("decision: PASS") == "PASS"
    assert parse_ai_decision("unclear text") == "PASS_WITH_WARNING"


def test_reviewer_report_generation_with_mocked_ollama(monkeypatch, tmp_path):
    def fake_ask(prompt, **kwargs):
        return {
            "available": True,
            "model_available": True,
            "endpoint": "http://localhost:11434/api/generate",
            "model": "llama3.1",
            "models": ["llama3.1:latest"],
            "response": "decision: PASS\nSummary: ready for human review.",
            "error": "",
        }

    validation_path = tmp_path / "validation.json"
    output_path = tmp_path / "AI_PHASE_REVIEW_REPORT.md"
    validation_path.write_text(json.dumps({"status": "PASS", "missing": [], "warnings": []}), encoding="utf-8")
    monkeypatch.setattr("scripts.ollama_phase_reviewer.ask_ollama", fake_ask)

    result = generate_review(phase="12.4.1", validation_path=validation_path, output_path=output_path)

    assert result["decision"] == "PASS"
    assert result["ollama_available"] is True
    assert result["auto_approve_production"] is False
    assert "Human review required" in output_path.read_text(encoding="utf-8")


def test_ask_ollama_model_missing(monkeypatch):
    def fake_list_models(ollama_url="http://localhost:11434", timeout=5):
        return {"available": True, "endpoint": "x", "models": ["mistral:latest"], "error": "", "status_code": 200}

    monkeypatch.setattr("scripts.ollama_phase_reviewer.list_ollama_models", fake_list_models)
    result = ask_ollama("hello", model="llama3.1")

    assert result["available"] is False
    assert result["model_available"] is False
    assert "not installed" in result["error"]

