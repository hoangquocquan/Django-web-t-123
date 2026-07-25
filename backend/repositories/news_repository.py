from database.connection import execute_write, query_all, query_one


def list_news_categories():
    return query_all("SELECT id, name, slug FROM news_categories ORDER BY id")


def list_paginated_news(filters, per_page, offset):
    keyword = filters["keyword"]
    where_parts = ["(news.title LIKE ? OR news.description LIKE ? OR news_categories.name LIKE ? OR news.tags_text LIKE ?)"]
    params = [keyword, keyword, keyword, keyword]
    if filters.get("category_id"):
        where_parts.append("news.category_id = ?")
        params.append(filters["category_id"])
    if filters.get("status"):
        where_parts.append("news.status = ?")
        params.append(filters["status"])
    where_sql = " AND ".join(where_parts)
    sort_sql = {
        "oldest": "news.published_at ASC, news.id ASC",
        "title": "news.title ASC",
        "featured": "news.is_featured DESC, news.published_at DESC, news.id DESC",
    }.get(filters.get("sort"), "news.published_at DESC, news.id DESC")
    total = query_one(
        f"""
        SELECT COUNT(*) AS total
        FROM news
        JOIN news_categories ON news_categories.id = news.category_id
        WHERE {where_sql}
        """,
        tuple(params),
    )["total"]
    items = query_all(
        f"""
        SELECT news.id, news.title, news.slug, news.image, news.thumbnail_url, news.description,
               news.published_at, news.scheduled_at, news.author, news.status, news.is_featured,
               news_categories.name AS category
        FROM news
        JOIN news_categories ON news_categories.id = news.category_id
        WHERE {where_sql}
        ORDER BY {sort_sql}
        LIMIT ? OFFSET ?
        """,
        tuple(params + [per_page, offset]),
    )
    return items, total


def get_news_record(news_id):
    return query_one(
        """
        SELECT id, category_id, title, slug, image, description, content, published_at,
               tags_text, seo_title, seo_description, thumbnail_url, author,
               scheduled_at, is_featured, status
        FROM news
        WHERE id = ?
        """,
        (news_id,),
    )


def insert_news(news):
    return execute_write(
        """
        INSERT INTO news (
          category_id, title, slug, image, description, content, tags_text,
          seo_title, seo_description, thumbnail_url, author, published_at,
          scheduled_at, is_featured, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            news["category_id"], news["title"], news["slug"], news["image"], news["description"], news["content"],
            news["tags_text"], news["seo_title"], news["seo_description"], news["thumbnail_url"],
            news["author"], news["published_at"], news["scheduled_at"], news["is_featured"], news["status"],
        ),
    )


def update_news_record(news_id, news):
    execute_write(
        """
        UPDATE news
        SET category_id = ?, title = ?, slug = ?, image = ?, description = ?, content = ?,
            tags_text = ?, seo_title = ?, seo_description = ?, thumbnail_url = ?,
            author = ?, published_at = ?, scheduled_at = ?, is_featured = ?, status = ?
        WHERE id = ?
        """,
        (
            news["category_id"], news["title"], news["slug"], news["image"], news["description"], news["content"],
            news["tags_text"], news["seo_title"], news["seo_description"], news["thumbnail_url"],
            news["author"], news["published_at"], news["scheduled_at"], news["is_featured"], news["status"], news_id,
        ),
    )


def delete_news_record(news_id):
    execute_write("DELETE FROM news WHERE id = ?", (news_id,))
