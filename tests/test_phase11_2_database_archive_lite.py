import sqlite3
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase11_2_database_archive_backup import create_backup_checkpoint
from scripts.phase11_2_database_archive_verify import verify_archive


def create_sqlite_database(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        connection.execute("INSERT INTO products (name) VALUES ('Training product')")
        connection.commit()
    finally:
        connection.close()
    return path


def test_metadata_generated(tmp_path):
    source = create_sqlite_database(tmp_path / "source.sqlite")
    result = create_backup_checkpoint(source_db=source, archive_root=tmp_path / "archive")

    metadata = result["metadata"]
    assert metadata["database_name"] == "source.sqlite"
    assert metadata["environment"] == "TRAINING"
    assert metadata["archive_type"] == "LEGACY_DATABASE_ARCHIVE"


def test_backup_package_created(tmp_path):
    source = create_sqlite_database(tmp_path / "source.sqlite")
    result = create_backup_checkpoint(source_db=source, archive_root=tmp_path / "archive")

    assert Path(result["artifacts"]["backup"]).exists()
    assert Path(result["artifacts"]["checksum"]).exists()
    assert Path(result["artifacts"]["manifest"]).exists()


def test_checksum_verification(tmp_path):
    source = create_sqlite_database(tmp_path / "source.sqlite")
    create_backup_checkpoint(source_db=source, archive_root=tmp_path / "archive")
    result = verify_archive(archive_root=tmp_path / "archive", review_report_path=tmp_path / "report.md")

    assert result["status"] == "ARCHIVE_VERIFIED"
    assert result["checks"]["checksum_valid"] is True


def test_archive_validation(tmp_path):
    source = create_sqlite_database(tmp_path / "source.sqlite")
    create_backup_checkpoint(source_db=source, archive_root=tmp_path / "archive")
    result = verify_archive(archive_root=tmp_path / "archive", review_report_path=tmp_path / "report.md")

    assert result["checks"]["archive_readable"] is True
    assert result["sqlite_integrity_check"] == "ok"
    assert result["final_status"] == "DATABASE_ARCHIVE_COMPLETE"


def test_rollback_document_exists():
    rollback_plan = PROJECT_ROOT / "docs" / "reviews" / "PHASE_11.2_DATABASE_ROLLBACK_PLAN.md"

    assert rollback_plan.exists()
    assert "Restore Procedure" in rollback_plan.read_text(encoding="utf-8")
