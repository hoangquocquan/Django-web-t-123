"""Che PII và secret trước khi ghi audit, error hoặc preview."""

from __future__ import annotations

import re


REDACTION_PATTERNS = (
    ("authorization", re.compile(r"(?i)\b(authorization\s*[:=]\s*(?:bearer\s+)?)[^\s,;]+"), r"\1[REDACTED]"),
    ("api_key", re.compile(r"(?i)\b(api[_ -]?key\s*[:=]\s*)[^\s,;]+"), r"\1[REDACTED]"),
    ("password", re.compile(r"(?i)\b(password|mật khẩu|mat khau)\s*[:=]\s*[^\s,;]+"), r"\1=[REDACTED]"),
    ("token", re.compile(r"(?i)\b(access[_ -]?token|reset[_ -]?token|token)\s*[:=]\s*[^\s,;]+"), r"\1=[REDACTED]"),
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE), "[REDACTED_EMAIL]"),
    ("phone", re.compile(r"(?<!\d)(?:\+?\d[\d .()-]{7,}\d)(?!\d)"), "[REDACTED_PHONE]"),
)


class AIRedactionService:
    """Redact chuỗi hoặc cấu trúc lồng nhau và trả summary không nhạy cảm."""

    def redact_text(self, value):
        text = str(value or "")
        summary = {}
        for name, pattern, replacement in REDACTION_PATTERNS:
            text, count = pattern.subn(replacement, text)
            if count:
                summary[name] = summary.get(name, 0) + count
        return text, summary

    def redact_value(self, value):
        summary = {}

        def merge(counts):
            for key, count in counts.items():
                summary[key] = summary.get(key, 0) + count

        def walk(item):
            if isinstance(item, dict):
                result = {}
                for key, nested in item.items():
                    if str(key).casefold() in {"authorization", "password", "token", "access_token", "api_key", "secret"}:
                        result[key] = "[REDACTED]"
                        summary[str(key).casefold()] = summary.get(str(key).casefold(), 0) + 1
                    else:
                        result[key] = walk(nested)
                return result
            if isinstance(item, (list, tuple)):
                return [walk(nested) for nested in item]
            if isinstance(item, str):
                redacted, counts = self.redact_text(item)
                merge(counts)
                return redacted
            return item

        return walk(value), summary
