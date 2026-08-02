"""Document processing pipeline for the MEC AI Knowledge Assistant."""

from __future__ import annotations

from pathlib import Path

from apps.knowledge.services.text_processing import TextProcessor
from apps.knowledge.services.upload_security import UploadSecurityService


class DocumentProcessor:
    """Extract, clean, and chunk supported knowledge documents."""

    def __init__(self, text_processor=None, upload_security=None):
        """Allow tests to inject a custom processor."""
        self.text_processor = text_processor or TextProcessor()
        self.upload_security = upload_security or UploadSecurityService()

    def process_text(self, content):
        """Process raw text into clean chunks."""
        cleaned = self.text_processor.clean_text(content)
        return {
            "text": cleaned,
            "chunks": self.text_processor.chunk_text(cleaned),
        }

    def process_file_path(self, file_path):
        """Process a local file path."""
        text = self.text_processor.extract_text(file_path)
        result = self.process_text(text)
        result["source_type"] = Path(file_path).suffix.lower().lstrip(".") or "text"
        result["source_path"] = str(file_path)
        return result

    def process_uploaded_file(self, uploaded_file):
        """Process a Django uploaded file."""
        validation = self.upload_security.validate(uploaded_file)
        filename = validation["filename"]
        text = self.text_processor.extract_uploaded_text(uploaded_file, filename)
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
        result = self.process_text(text)
        result["source_type"] = Path(filename).suffix.lower().lstrip(".") or "text"
        result["source_path"] = filename
        return result
