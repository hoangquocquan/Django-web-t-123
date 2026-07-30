"""Text extraction and chunking utilities for local RAG ingestion."""

from __future__ import annotations

import re
import zipfile
from html import unescape
from io import BytesIO
from pathlib import Path


SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown", ".pdf", ".docx"}


class TextProcessor:
    """Extract plain text and split it into stable chunks."""

    def extract_text(self, file_path):
        """Extract text from supported document types without external services."""
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported document type: {suffix}")
        raw_bytes = path.read_bytes()
        if suffix in {".txt", ".md", ".markdown"}:
            return raw_bytes.decode("utf-8", errors="replace")
        if suffix == ".docx":
            return self._extract_docx_text(path)
        if suffix == ".pdf":
            return self._extract_pdf_text(raw_bytes)
        return raw_bytes.decode("utf-8", errors="ignore")

    def extract_uploaded_text(self, uploaded_file, filename):
        """Extract text from a Django uploaded file object."""
        suffix = Path(filename or "").suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported document type: {suffix}")
        raw_bytes = uploaded_file.read()
        if suffix in {".txt", ".md", ".markdown"}:
            return raw_bytes.decode("utf-8", errors="replace")
        if suffix == ".docx":
            return self._extract_docx_text_from_bytes(raw_bytes)
        if suffix == ".pdf":
            return self._extract_pdf_text(raw_bytes)
        return raw_bytes.decode("utf-8", errors="ignore")

    def chunk_text(self, text, chunk_size=800, overlap=120):
        """Split text into overlapping chunks for retrieval."""
        normalized = " ".join(str(text or "").split())
        if not normalized:
            return []
        chunks = []
        start = 0
        while start < len(normalized):
            end = start + chunk_size
            chunks.append(normalized[start:end])
            if end >= len(normalized):
                break
            start = max(0, end - overlap)
        return chunks

    def clean_text(self, text):
        """Remove repeated whitespace and common prompt-injection markers."""
        normalized = " ".join(str(text or "").split())
        blocked_phrases = ["ignore previous instructions", "ignore all previous instructions"]
        for phrase in blocked_phrases:
            normalized = normalized.replace(phrase, "[removed unsafe instruction]")
        return normalized

    def _extract_docx_text(self, path):
        """Extract text from a DOCX file using the standard zip container."""
        return self._extract_docx_text_from_bytes(path.read_bytes())

    def _extract_docx_text_from_bytes(self, raw_bytes):
        """Extract text from DOCX bytes without adding a runtime dependency."""
        with zipfile.ZipFile(BytesIO(raw_bytes)) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
        text = re.sub(r"<[^>]+>", " ", xml)
        return unescape(" ".join(text.split()))

    def _extract_pdf_text(self, raw_bytes):
        """Best-effort PDF extraction for local demos and tests."""
        decoded = raw_bytes.decode("latin-1", errors="ignore")
        candidates = re.findall(r"\(([^()]*)\)", decoded)
        if candidates:
            return " ".join(unescape(item) for item in candidates)
        return decoded
