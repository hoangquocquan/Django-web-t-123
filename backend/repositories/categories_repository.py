from database.connection import execute_write, query_all, query_one


def list_paginated_categories(keyword, per_page, offset):
    total = query_one(
        "SELECT COUNT(*) AS total FROM product_categories WHERE name LIKE ? OR slug LIKE ?",
        (keyword, keyword),
    )["total"]
    items = query_all(
        """
        SELECT id, name, slug, description, sort_order
        FROM product_categories
        WHERE name LIKE ? OR slug LIKE ?
        ORDER BY sort_order, id DESC
        LIMIT ? OFFSET ?
        """,
        (keyword, keyword, per_page, offset),
    )
    return items, total


def get_category_record(category_id):
    return query_one(
        "SELECT id, name, slug, description, sort_order FROM product_categories WHERE id = ?",
        (category_id,),
    )


def insert_category(category):
    return execute_write(
        """
        INSERT INTO product_categories (name, slug, description, sort_order)
        VALUES (?, ?, ?, ?)
        """,
        (category["name"], category["slug"], category["description"], category["sort_order"]),
    )


def update_category(category_id, category):
    execute_write(
        """
        UPDATE product_categories
        SET name = ?, slug = ?, description = ?, sort_order = ?
        WHERE id = ?
        """,
        (category["name"], category["slug"], category["description"], category["sort_order"], category_id),
    )


def delete_category_record(category_id):
    execute_write("DELETE FROM product_categories WHERE id = ?", (category_id,))

