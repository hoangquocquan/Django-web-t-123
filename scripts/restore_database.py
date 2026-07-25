from pathlib import Path
import shutil
import sys


# Restore database từ file backup.
# Cách chạy: python scripts\restore_database.py backups\mecprecision-YYYYMMDD-HHMMSS.sqlite
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "backend" / "database" / "mecprecision.sqlite"


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts\\restore_database.py <backup-file.sqlite>")
        raise SystemExit(1)
    backup_path = Path(sys.argv[1]).resolve()
    if not backup_path.exists():
        print(f"Backup file not found: {backup_path}")
        raise SystemExit(1)
    shutil.copy2(backup_path, DATABASE_PATH)
    print(f"Database restored from: {backup_path}")


if __name__ == "__main__":
    main()

