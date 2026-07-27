"""Phase 11.2 lightweight legacy database archive backup tool.

The tool copies the local legacy SQLite database into a training archive folder,
calculates a checksum, and writes audit metadata. It never deletes or modifies
the source database.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_DB = PROJECT_ROOT / "backend" / "database" / "mecprecision.sqlite"
DEFAULT_ARCHIVE_ROOT = PROJECT_ROOT / "docs" / "migration" / "database_archive"


def utc_now():
    """Return an ISO timestamp for audit records."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def timestamp_for_filename():
    """Return a timestamp that is safe for filenames."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def get_source_version(project_root=None):
    """Return the current Git commit hash when Git is available."""
    root = Path(project_root or PROJECT_ROOT)
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN"


def sha256_file(path):
    """Calculate SHA-256 checksum for a file."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sqlite_integrity_check(path):
    """Open SQLite in read-only mode and run PRAGMA integrity_check."""
    database_path = Path(path).resolve()
    connection = sqlite3.connect(f"file:{database_path.as_posix()}?mode=ro", uri=True)
    try:
        result = connection.execute("PRAGMA integrity_check").fetchone()
        return result[0] if result else "missing_integrity_result"
    finally:
        connection.close()


def ensure_archive_structure(archive_root):
    """Create the archive folder structure."""
    root = Path(archive_root)
    paths = {
        "root": root,
        "backup": root / "backup",
        "metadata": root / "metadata",
        "reports": root / "reports",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def write_json(path, payload):
    """Write JSON using UTF-8 formatting."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path


def create_backup_checkpoint(source_db=None, archive_root=None, owner="migration-training-operator"):
    """Copy the legacy database and generate archive metadata."""
    source_path = Path(source_db or DEFAULT_SOURCE_DB)
    paths = ensure_archive_structure(archive_root or DEFAULT_ARCHIVE_ROOT)

    if not source_path.exists():
        raise FileNotFoundError(f"Source database does not exist: {source_path}")

    created_at = utc_now()
    stamp = timestamp_for_filename()
    backup_path = paths["backup"] / f"mecprecision-legacy-archive-{stamp}.sqlite"
    checksum_path = paths["backup"] / f"{backup_path.name}.sha256"
    manifest_path = paths["metadata"] / "archive_package_manifest.json"
    metadata_path = paths["root"] / "archive_metadata.json"
    checkpoint_path = paths["reports"] / "BACKUP_CHECKPOINT.json"

    source_checksum_before = sha256_file(source_path)
    shutil.copy2(source_path, backup_path)
    backup_checksum = sha256_file(backup_path)
    source_checksum_after = sha256_file(source_path)
    integrity_result = sqlite_integrity_check(backup_path)

    checksum_path.write_text(f"{backup_checksum}  {backup_path.name}\n", encoding="utf-8")

    metadata = {
        "database_name": source_path.name,
        "environment": "TRAINING",
        "archive_type": "LEGACY_DATABASE_ARCHIVE",
        "created_date": created_at,
        "source_version": get_source_version(),
        "backup_location": str(backup_path),
        "verification_status": "PENDING",
        "owner": owner,
    }

    manifest = {
        "phase": "11.2",
        "created_at": created_at,
        "source_database": str(source_path),
        "backup_location": str(backup_path),
        "checksum_location": str(checksum_path),
        "metadata_location": str(metadata_path),
        "backup_size_bytes": backup_path.stat().st_size,
        "source_checksum_before": source_checksum_before,
        "source_checksum_after": source_checksum_after,
        "backup_checksum": backup_checksum,
        "source_database_modified": source_checksum_before != source_checksum_after,
        "sqlite_integrity_check": integrity_result,
        "archive_package_type": "directory_manifest",
        "database_file_committed_to_git": False,
    }

    checkpoint = {
        "phase": "11.2",
        "status": "BACKUP_CHECKPOINT_CREATED",
        "created_at": created_at,
        "metadata": metadata,
        "manifest": manifest,
        "safety": {
            "source_database_deleted": False,
            "source_database_modified": source_checksum_before != source_checksum_after,
            "production_database_modified": False,
            "irreversible_migration_executed": False,
        },
    }

    write_json(metadata_path, metadata)
    write_json(manifest_path, manifest)
    write_json(checkpoint_path, checkpoint)

    checkpoint["artifacts"] = {
        "backup": str(backup_path),
        "checksum": str(checksum_path),
        "metadata": str(metadata_path),
        "manifest": str(manifest_path),
        "checkpoint": str(checkpoint_path),
    }
    write_json(checkpoint_path, checkpoint)
    return checkpoint


def main():
    """Command line entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Phase 11.2 legacy database archive backup")
    parser.add_argument("--source-db", default=None, help="SQLite source database path.")
    parser.add_argument("--archive-root", default=None, help="Archive output root.")
    parser.add_argument("--owner", default="migration-training-operator", help="Archive owner.")
    args = parser.parse_args()

    result = create_backup_checkpoint(source_db=args.source_db, archive_root=args.archive_root, owner=args.owner)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
