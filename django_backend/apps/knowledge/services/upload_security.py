"""Fail-closed validation and cleanup contracts for knowledge uploads."""

from __future__ import annotations

import mimetypes
import zipfile
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path, PurePosixPath

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage

MAGIC_PREFIXES = {
    ".pdf": (b"%PDF-",),
    ".docx": (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"),
}
TEXT_EXTENSIONS = {".txt", ".md", ".markdown"}
ALLOWED_EXTENSIONS = TEXT_EXTENSIONS | set(MAGIC_PREFIXES)
ALLOWED_MIME_TYPES = {
    ".txt": {"text/plain", "application/octet-stream"},
    ".md": {"text/markdown", "text/plain", "application/octet-stream"},
    ".markdown": {"text/markdown", "text/plain", "application/octet-stream"},
    ".pdf": {"application/pdf", "application/octet-stream"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
        "application/octet-stream",
    },
}


class MalwareScanner:
    """Contract for a local scanner; production can inject a ClamAV adapter."""

    def scan(self, filename, content):
        """Reject the standard EICAR signature; return a clean verdict otherwise."""
        if b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE" in content:
            raise ValidationError("Upload failed malware scanning.")
        return {"clean": True, "engine": "local-contract"}


class UploadSecurityService:
    """Validate an uploaded file before extraction or persistent storage."""

    def __init__(self, scanner=None):
        self.scanner = scanner or MalwareScanner()

    def validate(self, uploaded_file):
        """Return verified bytes and normalized metadata, restoring stream position."""
        filename = Path(getattr(uploaded_file, "name", "") or "").name
        if not filename or filename in {".", ".."}:
            raise ValidationError("A safe filename is required.")
        extension = Path(filename).suffix.casefold()
        if extension not in ALLOWED_EXTENSIONS:
            raise ValidationError("Unsupported document extension.")
        max_bytes = int(getattr(settings, "UPLOAD_MAX_BYTES", 10 * 1024 * 1024))
        declared_size = int(getattr(uploaded_file, "size", 0) or 0)
        if declared_size > max_bytes:
            raise ValidationError("Uploaded file is too large.")
        content = uploaded_file.read(max_bytes + 1)
        if len(content) > max_bytes:
            raise ValidationError("Uploaded file is too large.")
        if not content:
            raise ValidationError("Uploaded file is empty.")
        content_type = str(getattr(uploaded_file, "content_type", "") or "").casefold()
        guessed_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        effective_type = content_type or guessed_type
        if effective_type not in ALLOWED_MIME_TYPES[extension]:
            raise ValidationError("Uploaded MIME type does not match the extension.")
        prefixes = MAGIC_PREFIXES.get(extension)
        if prefixes and not content.startswith(prefixes):
            raise ValidationError(
                "Uploaded file signature does not match the extension."
            )
        if extension == ".docx":
            self._validate_docx_archive(content)
        verdict = self.scanner.scan(filename, content)
        if not verdict.get("clean"):
            raise ValidationError("Upload failed malware scanning.")
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
        return {
            "filename": filename,
            "extension": extension,
            "size": len(content),
            "content": content,
        }

    def _validate_docx_archive(self, content):
        """Reject traversal, encrypted archives, excessive members, and zip bombs."""
        try:
            archive = zipfile.ZipFile(BytesIO(content))
        except zipfile.BadZipFile as exc:
            raise ValidationError("Invalid DOCX archive.") from exc
        infos = archive.infolist()
        max_members = int(getattr(settings, "UPLOAD_ARCHIVE_MAX_MEMBERS", 500))
        max_uncompressed = int(
            getattr(settings, "UPLOAD_ARCHIVE_MAX_UNCOMPRESSED_BYTES", 50 * 1024 * 1024)
        )
        if len(infos) > max_members:
            raise ValidationError("Archive contains too many files.")
        total_size = sum(info.file_size for info in infos)
        compressed_size = max(1, sum(info.compress_size for info in infos))
        ratio_limit = int(getattr(settings, "UPLOAD_ARCHIVE_MAX_RATIO", 100))
        if total_size > max_uncompressed or total_size / compressed_size > ratio_limit:
            raise ValidationError("Archive expansion limit exceeded.")
        for info in infos:
            path = PurePosixPath(info.filename.replace("\\", "/"))
            if info.flag_bits & 0x1 or path.is_absolute() or ".." in path.parts:
                raise ValidationError("Unsafe archive member detected.")
        if "word/document.xml" not in {info.filename for info in infos}:
            raise ValidationError("DOCX document content is missing.")


@contextmanager
def stored_file_cleanup(storage_path):
    """Delete a newly stored file when downstream database work raises an error."""
    try:
        yield storage_path
    except Exception:
        if storage_path and default_storage.exists(storage_path):
            default_storage.delete(storage_path)
        raise
