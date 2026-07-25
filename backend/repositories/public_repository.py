from database.connection import query_all


def list_featured_product_overview():
    """Lấy danh sách sản phẩm nổi bật cho trang chủ."""
    return query_all(
        """
        SELECT
          id,
          name,
          slug,
          category_name AS category,
          main_image AS image,
          short_description AS description
        FROM product_overview
        WHERE is_featured = 1 AND status = 'published'
        ORDER BY sort_order, id
        """
    )


def list_capabilities():
    """Lấy các năng lực sản xuất hiển thị ở trang chủ và trang công nghệ."""
    return query_all(
        """
        SELECT title, content AS text, icon_label AS icon
        FROM capabilities
        ORDER BY sort_order, id
        """
    )


def list_news(limit=None):
    """Lấy tin tức kèm tên danh mục; limit dùng để giới hạn số bài."""
    limit_sql = "" if limit is None else "LIMIT ?"
    params = () if limit is None else (limit,)
    return query_all(
        f"""
        SELECT
          news.id,
          news.title,
          news.slug,
          news.image,
          news.description,
          news_categories.name AS category
        FROM news
        JOIN news_categories ON news_categories.id = news.category_id
        WHERE news.status = 'published'
          AND (news.scheduled_at IS NULL OR news.scheduled_at = '' OR datetime(news.scheduled_at) <= datetime('now'))
        ORDER BY news.published_at DESC, news.id DESC
        {limit_sql}
        """,
        params,
    )
