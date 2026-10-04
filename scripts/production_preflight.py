"""Fail-closed, secret-safe production environment validation."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    reason: str


def _bool(name: str) -> tuple[bool | None, str]:
    value = os.getenv(name, "").strip().casefold()
    if value not in {"true", "false"}:
        return None, "must be explicitly true or false"
    return value == "true", "configured"


def evaluate() -> list[Check]:
    checks: list[Check] = []
    secret = os.getenv("SECRET_KEY", "")
    checks.append(Check("SECRET_KEY", len(secret) >= 32 and "CHANGE_ME" not in secret.upper(), "strong value configured" if len(secret) >= 32 else "missing or too short"))

    hosts = [item.strip() for item in os.getenv("ALLOWED_HOSTS", "").split(",") if item.strip()]
    checks.append(Check("ALLOWED_HOSTS", bool(hosts) and all(host != "*" and "://" not in host and "/" not in host for host in hosts), "explicit hosts configured" if hosts else "missing"))

    for name, schemes in (
        ("DATABASE_URL", {"postgres", "postgresql"}),
        ("REDIS_URL", {"rediss"}),
    ):
        parsed = urlparse(os.getenv(name, ""))
        passed = (
            parsed.scheme in schemes
            and bool(parsed.hostname and parsed.password)
            and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
        )
        checks.append(Check(name, passed, "secure service URL configured" if passed else "missing or unsafe service URL"))

    sslmode = os.getenv("DATABASE_SSLMODE", "").casefold()
    checks.append(Check("DATABASE_SSLMODE", sslmode in {"require", "verify-full"}, "TLS required" if sslmode in {"require", "verify-full"} else "must be require or verify-full"))

    csrf = [item.strip() for item in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if item.strip()]
    checks.append(Check("CSRF_TRUSTED_ORIGINS", bool(csrf) and all(item.startswith("https://") and "*" not in item for item in csrf), "HTTPS origins configured" if csrf else "missing"))

    token = os.getenv("METRICS_BEARER_TOKEN", "")
    checks.append(Check("METRICS_BEARER_TOKEN", len(token) >= 24, "strong value configured" if len(token) >= 24 else "missing or too short"))

    for name, expected in (
        ("LINE_SEND_ENABLED", False),
        ("LEGACY_DATABASE_ENABLED", False),
        ("MEDIA_STORAGE_DURABLE", True),
        ("MEDIA_BACKUP_ENABLED", True),
    ):
        value, reason = _bool(name)
        checks.append(Check(name, value is expected, reason if value is expected else f"must be {str(expected).lower()}"))

    ai_values = {}
    for name in (
        "AI_SALES_OLLAMA_ENABLED",
        "AI_AGENT_OLLAMA_PLANNER_ENABLED",
        "AI_REDIS_RATE_LIMIT_ENABLED",
        "AI_OLLAMA_CAPACITY_ENABLED",
    ):
        value, reason = _bool(name)
        ai_values[name] = value
        checks.append(Check(name, value is not None, reason))

    if any(
        ai_values.get(name)
        for name in (
            "AI_SALES_OLLAMA_ENABLED",
            "AI_AGENT_OLLAMA_PLANNER_ENABLED",
            "AI_OLLAMA_CAPACITY_ENABLED",
        )
    ):
        provider = urlparse(os.getenv("OLLAMA_HOST", ""))
        provider_ok = (
            provider.scheme in {"http", "https"}
            and bool(provider.hostname)
            and provider.hostname not in {"localhost", "127.0.0.1", "::1"}
        )
        checks.append(
            Check(
                "OLLAMA_HOST",
                provider_ok,
                "provider configured" if provider_ok else "missing or local provider",
            )
        )

    checks.append(Check("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE") == "config.settings.production", "production settings selected" if os.getenv("DJANGO_SETTINGS_MODULE") == "config.settings.production" else "must select config.settings.production"))
    return checks


def main() -> int:
    checks = evaluate()
    print(json.dumps({"status": "PASS" if all(item.passed for item in checks) else "FAIL", "checks": [{"name": item.name, "status": "PASS" if item.passed else "FAIL", "reason": item.reason} for item in checks]}, indent=2))
    return 0 if all(item.passed for item in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
