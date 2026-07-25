from database.connection import execute_write, query_all, query_one, transaction


def list_paginated(table, searchable_columns, keyword, per_page, offset, order_by="id DESC"):
    """Danh sách phân trang dùng chung cho các module CMS nhỏ."""
    where_sql = " OR ".join([f"{column} LIKE ?" for column in searchable_columns])
    params = tuple([keyword] * len(searchable_columns))
    total = query_one(f"SELECT COUNT(*) AS total FROM {table} WHERE {where_sql}", params)["total"]
    items = query_all(
        f"SELECT * FROM {table} WHERE {where_sql} ORDER BY {order_by} LIMIT ? OFFSET ?",
        params + (per_page, offset),
    )
    return items, total


def get_record(table, record_id):
    """Lấy một bản ghi theo id."""
    return query_one(f"SELECT * FROM {table} WHERE id = ?", (record_id,))


def get_public_page_by_slug(slug):
    """Lấy trang động đã publish để hiển thị ngoài website."""
    return query_one(
        """
        SELECT title, slug, content, seo_title, seo_description
        FROM cms_pages
        WHERE slug = ? AND status = 'published'
        """,
        (slug,),
    )


def list_active_banners(placement):
    """Lấy banner đang publish theo vị trí hiển thị."""
    return query_all(
        """
        SELECT title, image_url, link_url, content
        FROM cms_banners
        WHERE placement = ? AND status = 'published'
        ORDER BY sort_order, id DESC
        """,
        (placement,),
    )


def delete_record(table, record_id):
    """Xóa một bản ghi theo id."""
    execute_write(f"DELETE FROM {table} WHERE id = ?", (record_id,))


def insert_page(page):
    return execute_write(
        """
        INSERT INTO cms_pages (title, slug, content, seo_title, seo_description, status, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (page["title"], page["slug"], page["content"], page["seo_title"], page["seo_description"], page["status"], page["sort_order"]),
    )


def update_page(page_id, page):
    execute_write(
        """
        UPDATE cms_pages
        SET title = ?, slug = ?, content = ?, seo_title = ?, seo_description = ?,
            status = ?, sort_order = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (page["title"], page["slug"], page["content"], page["seo_title"], page["seo_description"], page["status"], page["sort_order"], page_id),
    )


def list_menu_items():
    return query_all("SELECT id, location, parent_id, label, url, sort_order, status FROM cms_menu_items ORDER BY location, parent_id, sort_order, id")


def insert_menu_item(item):
    return execute_write(
        """
        INSERT INTO cms_menu_items (location, parent_id, label, url, sort_order, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (item["location"], item["parent_id"], item["label"], item["url"], item["sort_order"], item["status"]),
    )


def update_menu_item(item_id, item):
    execute_write(
        """
        UPDATE cms_menu_items
        SET location = ?, parent_id = ?, label = ?, url = ?, sort_order = ?, status = ?
        WHERE id = ?
        """,
        (item["location"], item["parent_id"], item["label"], item["url"], item["sort_order"], item["status"], item_id),
    )


def insert_banner(banner):
    return execute_write(
        """
        INSERT INTO cms_banners (title, placement, image_url, link_url, content, sort_order, status, starts_at, ends_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            banner["title"], banner["placement"], banner["image_url"], banner["link_url"], banner["content"],
            banner["sort_order"], banner["status"], banner["starts_at"], banner["ends_at"],
        ),
    )


def update_banner(banner_id, banner):
    execute_write(
        """
        UPDATE cms_banners
        SET title = ?, placement = ?, image_url = ?, link_url = ?, content = ?,
            sort_order = ?, status = ?, starts_at = ?, ends_at = ?
        WHERE id = ?
        """,
        (
            banner["title"], banner["placement"], banner["image_url"], banner["link_url"], banner["content"],
            banner["sort_order"], banner["status"], banner["starts_at"], banner["ends_at"], banner_id,
        ),
    )


def list_quotes(keyword, per_page, offset):
    total = query_one(
        """
        SELECT COUNT(*) AS total
        FROM quote_requests
        JOIN customers ON customers.id = quote_requests.customer_id
        WHERE quote_requests.project_name LIKE ? OR customers.company_name LIKE ? OR customers.contact_name LIKE ? OR quote_requests.status LIKE ?
        """,
        (keyword, keyword, keyword, keyword),
    )["total"]
    items = query_all(
        """
        SELECT quote_requests.*, customers.company_name, customers.contact_name, customers.email, customers.phone,
               admin_users.full_name AS assigned_name
        FROM quote_requests
        JOIN customers ON customers.id = quote_requests.customer_id
        LEFT JOIN admin_users ON admin_users.id = quote_requests.assigned_to
        WHERE quote_requests.project_name LIKE ? OR customers.company_name LIKE ? OR customers.contact_name LIKE ? OR quote_requests.status LIKE ?
        ORDER BY quote_requests.id DESC
        LIMIT ? OFFSET ?
        """,
        (keyword, keyword, keyword, keyword, per_page, offset),
    )
    return items, total


def update_quote(quote_id, quote):
    execute_write(
        """
        UPDATE quote_requests
        SET status = ?, assigned_to = ?, internal_note = ?, quoted_at = ?, completed_at = ?
        WHERE id = ?
        """,
        (quote["status"], quote["assigned_to"], quote["internal_note"], quote["quoted_at"], quote["completed_at"], quote_id),
    )


def list_admin_options():
    return query_all("SELECT id, full_name, email FROM admin_users WHERE is_active = 1 ORDER BY full_name")


def insert_customer(customer):
    return execute_write(
        """
        INSERT INTO customers (company_name, contact_name, email, phone, country)
        VALUES (?, ?, ?, ?, ?)
        """,
        (customer["company_name"], customer["contact_name"], customer["email"], customer["phone"], customer["country"]),
    )


def update_customer(customer_id, customer):
    execute_write(
        """
        UPDATE customers
        SET company_name = ?, contact_name = ?, email = ?, phone = ?, country = ?
        WHERE id = ?
        """,
        (customer["company_name"], customer["contact_name"], customer["email"], customer["phone"], customer["country"], customer_id),
    )


def insert_quote_request_with_item(customer, quote, item, files):
    """Tạo customer + quote request + item + file trong một transaction."""
    with transaction() as connection:
        cursor = connection.execute(
            """
            INSERT INTO customers (company_name, contact_name, email, phone, country)
            VALUES (?, ?, ?, ?, ?)
            """,
            (customer["company_name"], customer["contact_name"], customer["email"], customer["phone"], customer["country"]),
        )
        customer_id = cursor.lastrowid
        cursor = connection.execute(
            """
            INSERT INTO quote_requests (customer_id, project_name, message, status)
            VALUES (?, ?, ?, 'new')
            """,
            (customer_id, quote["project_name"], quote["message"]),
        )
        quote_id = cursor.lastrowid
        connection.execute(
            """
            INSERT INTO quote_request_items (quote_request_id, drawing_code, quantity, tolerance, note)
            VALUES (?, ?, ?, ?, ?)
            """,
            (quote_id, item["drawing_code"], item["quantity"], item["tolerance"], item["note"]),
        )
        for file_info in files:
            if file_info.get("file_url"):
                connection.execute(
                    """
                    INSERT INTO quote_files (quote_request_id, file_name, file_url, file_type)
                    VALUES (?, ?, ?, ?)
                    """,
                    (quote_id, file_info["file_name"], file_info["file_url"], file_info.get("file_type", "")),
                )
        return quote_id


def insert_customer_note(customer_id, note, created_by):
    return execute_write(
        "INSERT INTO customer_notes (customer_id, note, created_by) VALUES (?, ?, ?)",
        (customer_id, note, created_by),
    )


def list_customer_notes(customer_id):
    return query_all("SELECT * FROM customer_notes WHERE customer_id = ? ORDER BY id DESC", (customer_id,))


def upsert_newsletter(subscriber):
    existing = query_one("SELECT id FROM newsletter_subscribers WHERE email = ?", (subscriber["email"],))
    if existing:
        execute_write(
            "UPDATE newsletter_subscribers SET status = ?, unsubscribed_at = ? WHERE email = ?",
            (subscriber["status"], subscriber["unsubscribed_at"], subscriber["email"]),
        )
        return existing["id"]
    return execute_write(
        "INSERT INTO newsletter_subscribers (email, status, unsubscribed_at) VALUES (?, ?, ?)",
        (subscriber["email"], subscriber["status"], subscriber["unsubscribed_at"]),
    )


def list_all_newsletter_subscribers():
    return query_all("SELECT email, status, subscribed_at, unsubscribed_at FROM newsletter_subscribers ORDER BY id DESC")
