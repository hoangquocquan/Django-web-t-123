"""Text extraction and chunking utilities for local RAG ingestion."""

from __future__ import annotations

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

