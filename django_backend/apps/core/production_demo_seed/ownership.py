"""Dataset ownership helpers for safe idempotency and validation."""

from __future__ import annotations

from .profiles import DATASET_MARKER, DATASET_PREFIX, SAFE_EMAIL_DOMAIN


def marker_text(extra: str = "") -> str:
    """Return a compact marker safe for text fields."""

    suffix = f"; {extra}" if extra else ""
    return f"dataset={DATASET_MARKER}{suffix}"


def owned_email(local_part: str) -> str:
    """Return a non-deliverable seed-owned email address."""

    safe = str(local_part).strip().lower().replace("_", ".")
    return f"{safe}@{SAFE_EMAIL_DOMAIN}"


def idempotency_key(kind: str, index: int | str) -> str:
    """Return a canonical-service-safe deterministic idempotency key."""

    return f"pdv1-{kind}-{index}"


def is_owned_email(value: str) -> bool:
    """Check whether an email belongs to this seed dataset."""

    return str(value or "").casefold().endswith(f"@{SAFE_EMAIL_DOMAIN}")


def prefixed(label: str, index: int | str) -> str:
    """Return a human-readable deterministic seed label."""

    return f"[{DATASET_PREFIX}] {label} {index}"
