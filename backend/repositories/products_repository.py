from database.connection import execute_write, query_all, query_one, transaction


def list_products():
    """Lấy toàn bộ sản phẩm kèm tên danh mục."""
    return query_all(
        """
        SELECT
          id,
          name,
          slug,
          category_name AS category,
          short_description AS description,
          main_image AS image,
          thumbnail_url,
          status,
          sort_order
        FROM product_overview
        WHERE status = 'published'
        ORDER BY sort_order, id
        """
    )


def list_paginated_products(filters, per_page, offset):
    """Lấy sản phẩm cho CMS, có tìm kiếm và phân trang."""
    keyword = filters["keyword"]
    where_parts = ["(name LIKE ? OR category_name LIKE ? OR short_description LIKE ? OR sku LIKE ?)"]
    params = [keyword, keyword, keyword, keyword]
    if filters.get("category_id"):
        where_parts.append("category_id = ?")
        params.append(filters["category_id"])
    if filters.get("status"):
        where_parts.append("status = ?")
        params.append(filters["status"])
    where_sql = " AND ".join(where_parts)
    sort_sql = {
        "oldest": "id ASC",
        "name": "name ASC",
        "price_desc": "price DESC, id DESC",
        "price_asc": "price ASC, id DESC",
        "sort_order": "sort_order, id DESC",
    }.get(filters.get("sort"), "id DESC")
    total = query_one(
        f"""
        SELECT COUNT(*) AS total
        FROM product_overview
        WHERE {where_sql}
        """,
        tuple(params),
    )["total"]
    items = query_all(
        f"""
        SELECT
          id,
          name,
          slug,
          category_name AS category,
          short_description,
          main_image,
          sku,
          price,
          thumbnail_url,
          status,
          sort_order
        FROM product_overview
        WHERE {where_sql}
        ORDER BY {sort_sql}
        LIMIT ? OFFSET ?
        """,
        tuple(params + [per_page, offset]),
    )
    return items, total


def list_product_categories():
    """Lấy toàn bộ danh mục sản phẩm."""
    return query_all(
        """
        SELECT id, name, slug, description
        FROM product_categories
        ORDER BY sort_order, id
        """
    )


def get_product_by_id(product_id):
    """Lấy một sản phẩm theo id từ view product_overview."""
    return query_one(
        """
        SELECT
          id,
          name,
          slug,
          category_name AS category,
          short_description AS description,
          main_image AS image,
          sku,
          price,
          thumbnail_url,
          pdf_url,
          video_url,
          tags_text,
          seo_title,
          seo_description,
          seo_keywords,
          canonical_url,
          og_image,
          robots,
          schema_json,
          related_product_ids,
          sort_order,
          status,
          published_at
        FROM product_overview
        WHERE id = ? AND status = 'published'
        """,
        (product_id,),
    )


def get_product_record(product_id):
    """Lấy bản ghi gốc trong bảng products."""
    return query_one(
        """
        SELECT id, category_id, name, slug, short_description, description, main_image, is_featured,
               sku, price, thumbnail_url, gallery_urls, pdf_url, video_url, tags_text,
               seo_title, seo_description, seo_keywords, canonical_url, og_image, robots, schema_json,
               related_product_ids, sort_order, status, published_at
        FROM products
        WHERE id = ?
        """,
        (product_id,),
    )


def product_category_exists(category_id):
    """Kiểm tra danh mục sản phẩm có tồn tại không."""
    return query_one("SELECT id FROM product_categories WHERE id = ?", (category_id,)) is not None


def insert_product(product):
    """Thêm sản phẩm mới và trả về id."""
    return execute_write(
        """
        INSERT INTO products (
          category_id, name, slug, short_description, description, main_image, is_featured,
          sku, price, thumbnail_url, gallery_urls, pdf_url, video_url, tags_text,
          seo_title, seo_description, seo_keywords, canonical_url, og_image, robots, schema_json,
          related_product_ids, sort_order, status, published_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product["category_id"],
            product["name"],
            product["slug"],
            product["short_description"],
            product["description"],
            product["main_image"],
            product["is_featured"],
            product["sku"],
            product["price"],
            product["thumbnail_url"],
            product["gallery_urls"],
            product["pdf_url"],
            product["video_url"],
            product["tags_text"],
            product["seo_title"],
            product["seo_description"],
            product["seo_keywords"],
            product["canonical_url"],
            product["og_image"],
            product["robots"],
            product["schema_json"],
            product["related_product_ids"],
            product["sort_order"],
            product["status"],
            product["published_at"],
        ),
    )


def update_product_record(product_id, product):
    """Cập nhật bản ghi sản phẩm."""
    execute_write(
        """
        UPDATE products
        SET category_id = ?,
            name = ?,
            slug = ?,
            short_description = ?,
            description = ?,
            main_image = ?,
            is_featured = ?,
            sku = ?,
            price = ?,
            thumbnail_url = ?,
            gallery_urls = ?,
            pdf_url = ?,
            video_url = ?,
            tags_text = ?,
            seo_title = ?,
            seo_description = ?,
            seo_keywords = ?,
            canonical_url = ?,
            og_image = ?,
            robots = ?,
            schema_json = ?,
            related_product_ids = ?,
            sort_order = ?,
            status = ?,
            published_at = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            product["category_id"],
            product["name"],
            product["slug"],
            product["short_description"],
            product["description"],
            product["main_image"],
            product["is_featured"],
            product["sku"],
            product["price"],
            product["thumbnail_url"],
            product["gallery_urls"],
            product["pdf_url"],
            product["video_url"],
            product["tags_text"],
            product["seo_title"],
            product["seo_description"],
            product["seo_keywords"],
            product["canonical_url"],
            product["og_image"],
            product["robots"],
            product["schema_json"],
            product["related_product_ids"],
            product["sort_order"],
            product["status"],
            product["published_at"],
            product_id,
        ),
    )


def delete_product_record(product_id):
    """Xóa sản phẩm và dữ liệu phụ liên kết."""
    # Xóa sản phẩm là thao tác nhiều bước nên dùng transaction.
    # Nếu xóa bảng phụ thành công nhưng xóa products lỗi, toàn bộ sẽ rollback.
    with transaction() as connection:
        for table in ("product_materials", "product_processes", "product_images", "product_specs"):
            connection.execute(f"DELETE FROM {table} WHERE product_id = ?", (product_id,))
        connection.execute("DELETE FROM products WHERE id = ?", (product_id,))
