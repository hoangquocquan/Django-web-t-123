from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_DIR = PROJECT_ROOT / "backend" / "database"
DATABASE_PATH = DATABASE_DIR / "mecprecision.sqlite"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"
SEED_PATH = DATABASE_DIR / "seed.sql"


def run_sql_file(connection, path):
    """Chạy toàn bộ câu lệnh SQL trong một file."""
    sql = path.read_text(encoding="utf-8")
    connection.executescript(sql)


def main():
    """Tạo lại database SQLite từ schema.sql và seed.sql."""
    if DATABASE_PATH.exists():
      DATABASE_PATH.unlink()

    connection = sqlite3.connect(DATABASE_PATH)
    try:
        run_sql_file(connection, SCHEMA_PATH)
        run_sql_file(connection, SEED_PATH)
        connection.commit()
    finally:
        connection.close()

    print(f"Database created: {DATABASE_PATH}")


if __name__ == "__main__":
    main()
