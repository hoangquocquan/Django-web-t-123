from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "backend" / "database" / "mecprecision.sqlite"

TABLES = [
    "admin_users",
    "product_categories",
    "materials",
    "machines",
    "manufacturing_processes",
    "products",
    "product_materials",
    "product_processes",
    "product_images",
    "product_specs",
    "capabilities",
    "capability_machines",
    "customers",
    "quote_requests",
    "quote_request_items",
    "quote_files",
    "news_categories",
    "news",
    "tags",
    "news_tags",
    "contact_requests",
]


def main():
    """In số lượng dữ liệu trong từng bảng để kiểm tra database."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.cursor()
        for table in TABLES:
            count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{count} {table}")

        overview_count = cursor.execute("SELECT COUNT(*) FROM product_overview").fetchone()[0]
        print(f"{overview_count} product_overview")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
