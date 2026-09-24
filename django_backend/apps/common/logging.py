"""Structured logging helpers for production operations."""

from __future__ import annotations

import json
import logging


class JsonLogFormatter(logging.Formatter):
    """Render a stable JSON log without request bodies, credentials, or PII."""

    SAFE_FIELDS = (
        "event",
        "correlation_id",
        "method",
        "route",
        "status_code",
        "duration_ms",
        "component",
        "outcome",
    )

    def format(self, record):
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in self.SAFE_FIELDS:
            value = getattr(record, field, None)
            if value not in (None, ""):
                payload[field] = value
        if record.exc_info:
            payload["exception"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
