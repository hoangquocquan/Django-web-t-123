"""Temporary submission store for Phase 11.1.1 API replacement contracts.

The service validates and records write intents inside Django API memory only.
It deliberately does not write to the legacy SQLite database while the legacy
shutdown and traffic cutover are still under review.
"""

from __future__ import annotations

import itertools
from copy import deepcopy
from datetime import datetime, timezone


_SUBMISSION_ID_SEQUENCE = itertools.count(1)
_SUBMISSIONS = []


def _now_iso():
    """Return an ISO timestamp for API responses."""
    return datetime.now(timezone.utc).isoformat()


def _clean_payload(payload):
    """Copy request data into a plain dict without mutating the DRF object."""
    return dict(payload or {})


def create_submission(submission_type, legacy_endpoint, operation, payload):
    """Create a safe Django-side write intent for a legacy API replacement."""
    submission = {
        "id": next(_SUBMISSION_ID_SEQUENCE),
        "submission_type": submission_type,
        "legacy_endpoint": legacy_endpoint,
        "operation": operation,
        "status": "accepted_for_django_processing",
        "payload": _clean_payload(payload),
        "created_at": _now_iso(),
    }
    _SUBMISSIONS.append(submission)
    return deepcopy(submission)


def list_submissions():
    """Return stored write intents for tests or diagnostics."""
    return deepcopy(_SUBMISSIONS)


def reset_submissions():
    """Clear the in-memory store; tests use this to stay isolated."""
    _SUBMISSIONS.clear()
