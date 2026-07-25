import sys
import time
from pathlib import Path


# Worker xử lý queue local.
# Chạy một lần: python scripts\run_worker.py
# Chạy liên tục: python scripts\run_worker.py --loop
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from database.migrations import ensure_cms_tables  # noqa: E402
from services.queue_service import process_pending_jobs  # noqa: E402


def main():
    ensure_cms_tables()
    loop = "--loop" in sys.argv
    while True:
        results = process_pending_jobs(limit=20)
        print(f"Processed jobs: {results}")
        if not loop:
            break
        time.sleep(5)


if __name__ == "__main__":
    main()

