from pathlib import Path
import shutil
from datetime import datetime


# Script background job đơn giản: có thể gọi bằng Task Scheduler/cron để backup SQLite.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "backend" / "database" / "mecprecision.sqlite"
BACKUP_ROOT = PROJECT_ROOT / "backups"


def main():
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = BACKUP_ROOT / f"mecprecision-{timestamp}.sqlite"
    shutil.copy2(DATABASE_PATH, backup_path)
    print(f"Backup created: {backup_path}")


if __name__ == "__main__":
    main()

