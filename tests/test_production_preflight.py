from __future__ import annotations

from scripts.production_preflight import evaluate


def _valid(monkeypatch):
    values = {
        "SECRET_KEY": "s" * 48,
        "ALLOWED_HOSTS": "app.example.test",
        "DATABASE_URL": "postgresql://user:password@db.example.test/app",
        "DATABASE_SSLMODE": "verify-full",
        "REDIS_URL": "rediss://:password@redis.example.test/0",
        "CSRF_TRUSTED_ORIGINS": "https://app.example.test",
        "METRICS_BEARER_TOKEN": "m" * 32,
        "LINE_SEND_ENABLED": "false",
        "LEGACY_DATABASE_ENABLED": "false",
        "MEDIA_STORAGE_DURABLE": "true",
        "MEDIA_BACKUP_ENABLED": "true",
        "AI_SALES_OLLAMA_ENABLED": "false",
        "AI_AGENT_OLLAMA_PLANNER_ENABLED": "false",
        "AI_REDIS_RATE_LIMIT_ENABLED": "true",
        "AI_OLLAMA_CAPACITY_ENABLED": "false",
        "DJANGO_SETTINGS_MODULE": "config.settings.production",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)


def test_valid_contract_passes_without_exposing_values(monkeypatch):
    _valid(monkeypatch)
    assert all(check.passed for check in evaluate())


def test_unsafe_switches_and_transport_fail(monkeypatch):
    _valid(monkeypatch)
    monkeypatch.setenv("LINE_SEND_ENABLED", "true")
    monkeypatch.setenv("DATABASE_SSLMODE", "prefer")
    monkeypatch.setenv("REDIS_URL", "redis://:password@redis.example.test/0")
    failed = {check.name for check in evaluate() if not check.passed}
    assert {"LINE_SEND_ENABLED", "DATABASE_SSLMODE", "REDIS_URL"} <= failed


def test_missing_identity_scope_fails_closed(monkeypatch):
    _valid(monkeypatch)
    monkeypatch.delenv("ALLOWED_HOSTS")
    assert not next(check for check in evaluate() if check.name == "ALLOWED_HOSTS").passed


def test_enabled_ai_requires_non_local_provider(monkeypatch):
    _valid(monkeypatch)
    monkeypatch.setenv("AI_SALES_OLLAMA_ENABLED", "true")
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")
    assert not next(check for check in evaluate() if check.name == "OLLAMA_HOST").passed

    monkeypatch.setenv("OLLAMA_HOST", "https://ollama.internal.example.test")
    assert next(check for check in evaluate() if check.name == "OLLAMA_HOST").passed
