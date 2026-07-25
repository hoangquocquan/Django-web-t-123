from pathlib import Path
import json
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "backend" / "database" / "mecprecision.sqlite"
OUTPUT_PATH = PROJECT_ROOT / "frontend" / "js" / "data.js"


def rows_to_dicts(cursor, query):
    """Chạy câu SQL và đổi kết quả thành danh sách object dễ dùng trong JavaScript."""
    rows = cursor.execute(query).fetchall()
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def main():
    """Xuất dữ liệu cần hiển thị ngoài website từ SQLite sang file data.js."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        cursor = connection.cursor()

        products = rows_to_dicts(
            cursor,
            """
            SELECT
              name,
              category_name AS category,
              main_image AS image,
              short_description AS description
            FROM product_overview
            WHERE is_featured = 1
            ORDER BY id
            """,
        )

        capabilities = rows_to_dicts(
            cursor,
            """
            SELECT
              title,
              content AS text,
              icon_label AS icon
            FROM capabilities
            ORDER BY sort_order, id
            """,
        )

        news = rows_to_dicts(
            cursor,
            """
            SELECT
              news.title,
              news.image,
              news.description,
              news_categories.name AS category
            FROM news
            JOIN news_categories ON news_categories.id = news.category_id
            ORDER BY news.published_at DESC, news.id DESC
            LIMIT 3
            """,
        )
    finally:
        connection.close()

    site_data = {
        "products": products,
        "capabilities": capabilities,
        "news": news,
    }

    # data.js dùng biến toàn cục window.siteData để HTML tĩnh có thể đọc được bằng thẻ <script>.
    content = "window.siteData = "
    content += json.dumps(site_data, ensure_ascii=False, indent=2)
    content += ";\n"
    OUTPUT_PATH.write_text(content, encoding="utf-8")
    print(f"Exported data: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
