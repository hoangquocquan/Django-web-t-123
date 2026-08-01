"""Chuẩn hóa input để policy scan không bị lách bằng Unicode hoặc khoảng trắng."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


ZERO_WIDTH_PATTERN = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]")
WHITESPACE_PATTERN = re.compile(r"\s+")
SPACED_CHAR_PATTERN = re.compile(r"(?<!\w)(?:[a-z0-9]\s+){3,}[a-z0-9](?!\w)", re.IGNORECASE)


@dataclass(frozen=True)
class NormalizedAIInput:
    """Giữ input gốc cho business flow và bản chuẩn hóa chỉ dùng cho policy."""

    original: str
    normalized: str
    scan_text: str
    zero_width_removed: bool
    spaced_characters_collapsed: bool


class AIInputNormalizer:
    """Áp dụng NFKC, casefold, bỏ zero-width và phát hiện chữ tách khoảng trắng."""

    def normalize(self, value) -> NormalizedAIInput:
        original = str(value or "")
        nfkc = unicodedata.normalize("NFKC", original)
        without_zero_width = ZERO_WIDTH_PATTERN.sub("", nfkc)
        normalized = WHITESPACE_PATTERN.sub(" ", without_zero_width.casefold()).strip()
        collapsed_matches = []

        def collapse(match):
            compact = re.sub(r"\s+", "", match.group(0))
            collapsed_matches.append(compact)
            return compact

        collapsed = SPACED_CHAR_PATTERN.sub(collapse, normalized)
        scan_text = f"{normalized}\n{collapsed}" if collapsed != normalized else normalized
        return NormalizedAIInput(
            original=original,
            normalized=normalized,
            scan_text=scan_text,
            zero_width_removed=without_zero_width != nfkc,
            spaced_characters_collapsed=bool(collapsed_matches),
        )
