"""Fail-closed environment and database gates for demo seed writes."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.conf import settings

ALLOWED_ENVIRONMENTS = frozenset({"DEV", "TEST", "STAGING", "UAT"})
ENVIRONMENT_SETTING = "DEMO_TOOLING_ENVIRONMENT"
DATABASE_ALLOWLIST_SETTING = "DEMO_TOOLING_DATABASE_ALLOWLIST"
SEED_ENABLE_SETTING = "PRODUCTION_DEMO_SEED_ALLOWED"
DB_CONFIRMATION_ENV = "PRODUCTION_DEMO_SEED_DATABASE_CONFIRMED"
PRODUCTION_MARKERS = ("prod", "production", "live", "primary")


@dataclass(frozen=True)
class SafetyResult:
    """Safety gate result used by commands and tests."""

    allowed: bool
    reasons: tuple[str, ...]


def effective_environment() -> str:
    """Return the explicit effective runtime environment."""

    value = getattr(settings, ENVIRONMENT_SETTING, None)
    if value is None:
        value = os.getenv(ENVIRONMENT_SETTING, "")
    return str(value).strip().upper()


def allow_environment() -> bool:
    """Allow only explicitly named non-production environments."""

    return effective_environment() in ALLOWED_ENVIRONMENTS


def _database_config() -> dict[str, Any]:
    return dict(settings.DATABASES.get("default", {}))


def _normalise_engine(value: str) -> str:
    value = str(value or "").casefold()
    if value.endswith("sqlite3"):
        return "sqlite"
    if value.endswith(("postgresql", "postgis")):
        return "postgresql"
    return value


def _resolved_path(value: str) -> str:
    """Resolve Windows drive paths emitted by sqlite URL parsers."""

    raw = str(value or "")
    if os.name == "nt" and re.match(r"^/[A-Za-z]:", raw):
        raw = raw[1:]
    return str(Path(raw).expanduser().resolve())


def database_identity() -> dict[str, str]:
    """Return the effective database identity without exposing credentials."""

    config = _database_config()
    engine = _normalise_engine(config.get("ENGINE", ""))
    name = str(config.get("NAME", ""))
    identity = {
        "engine": engine,
        "host": str(config.get("HOST", "")),
        "port": str(config.get("PORT", "")),
        "name": name,
    }
    if engine == "sqlite" and name:
        identity["path"] = _resolved_path(name)
    return identity


def _allowlist() -> list[dict[str, Any]]:
    value = getattr(settings, DATABASE_ALLOWLIST_SETTING, None)
    if not isinstance(value, (list, tuple)):
        return []
    return [item for item in value if isinstance(item, dict)]


def _matches(identity: dict[str, str], candidate: dict[str, Any]) -> bool:
    engine = _normalise_engine(candidate.get("engine", ""))
    if not engine or identity.get("engine") != engine:
        return False
    if engine == "sqlite":
        expected = candidate.get("path", candidate.get("name"))
        if not expected:
            return False
        return identity.get("path") == _resolved_path(str(expected))
    return (
        identity.get("host") == str(candidate.get("host", ""))
        and identity.get("port") == str(candidate.get("port", ""))
        and identity.get("name") == str(candidate.get("name", ""))
    )


def _identity_is_non_production(identity: dict[str, str], candidate: dict[str, Any]) -> bool:
    """Reject production-looking names and unknown remote hosts."""

    if candidate.get("non_production") is False:
        return False
    host = identity.get("host", "").strip().casefold()
    if host and host not in {"localhost", "127.0.0.1", "::1"} and not candidate.get("non_production"):
        return False
    searchable = " ".join(
        identity.get(key, "").casefold() for key in ("host", "name", "path")
    )
    return not any(marker in searchable for marker in PRODUCTION_MARKERS)


def allow_database() -> bool:
    """Allow only an exact, explicitly configured non-production identity."""

    identity = database_identity()
    return bool(identity.get("engine")) and any(
        _matches(identity, candidate) and _identity_is_non_production(identity, candidate)
        for candidate in _allowlist()
    )


def seed_enabled() -> bool:
    """Return the explicit seed-enable setting without accepting truthy noise."""

    value = getattr(settings, SEED_ENABLE_SETTING, None)
    if value is None:
        value = os.getenv(SEED_ENABLE_SETTING, "")
    if isinstance(value, bool):
        return value
    return str(value).strip().casefold() == "true"


def evaluate_safety(*, apply: bool) -> SafetyResult:
    """Evaluate every gate before an apply can enter the transaction."""

    if not apply:
        return SafetyResult(allowed=True, reasons=())

    reasons: list[str] = []
    if not allow_environment():
        reasons.append(f"{ENVIRONMENT_SETTING} must be one of DEV, TEST, STAGING, or UAT.")
    if not allow_database():
        reasons.append(f"{DATABASE_ALLOWLIST_SETTING} must exactly allow the effective database.")
    if not seed_enabled():
        reasons.append(f"{SEED_ENABLE_SETTING}=true is required for --apply.")
    if os.getenv(DB_CONFIRMATION_ENV, "").strip().casefold() not in {"", "local-disposable"}:
        reasons.append(f"{DB_CONFIRMATION_ENV} has an invalid value.")
    return SafetyResult(allowed=not reasons, reasons=tuple(reasons))


def require_safe_apply() -> None:
    """Raise a command error before any write when an apply gate fails."""

    result = evaluate_safety(apply=True)
    if not result.allowed:
        from django.core.management.base import CommandError

        raise CommandError("; ".join(result.reasons))
