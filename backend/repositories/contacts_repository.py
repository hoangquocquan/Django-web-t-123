from database.connection import execute_write, query_all, query_one


def list_recent_contacts(limit=10):
    return query_all(
        """
        SELECT id, name, contact, company, phone, email, country, interested_product, attachment_url, message, status, is_read, note, created_at
        FROM contact_requests
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    )


def list_paginated_contacts(keyword, per_page, offset):
    total = query_one(
        """
        SELECT COUNT(*) AS total FROM contact_requests
        WHERE name LIKE ? OR contact LIKE ? OR company LIKE ? OR email LIKE ? OR phone LIKE ? OR interested_product LIKE ? OR message LIKE ? OR status LIKE ?
        """,
        (keyword, keyword, keyword, keyword, keyword, keyword, keyword, keyword),
    )["total"]
    items = query_all(
        """
        SELECT id, name, contact, company, phone, email, country, interested_product, attachment_url, message, status, is_read, note, created_at
        FROM contact_requests
        WHERE name LIKE ? OR contact LIKE ? OR company LIKE ? OR email LIKE ? OR phone LIKE ? OR interested_product LIKE ? OR message LIKE ? OR status LIKE ?
        ORDER BY created_at DESC, id DESC
        LIMIT ? OFFSET ?
        """,
        (keyword, keyword, keyword, keyword, keyword, keyword, keyword, keyword, per_page, offset),
    )
    return items, total


def get_contact_record(contact_id):
    return query_one("SELECT * FROM contact_requests WHERE id = ?", (contact_id,))


def insert_contact(contact):
    return execute_write(
        """
        INSERT INTO contact_requests (
          name, contact, company, phone, email, country, interested_product, attachment_url,
          message, status, is_read, note
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            contact["name"], contact["contact"], contact["company"], contact["phone"], contact["email"],
            contact["country"], contact["interested_product"], contact["attachment_url"],
            contact["message"], contact["status"], contact["is_read"], contact["note"],
        ),
    )


def update_contact_record(contact_id, contact):
    execute_write(
        """
        UPDATE contact_requests
        SET name = ?, contact = ?, company = ?, phone = ?, email = ?, country = ?,
            interested_product = ?, attachment_url = ?, message = ?, status = ?, is_read = ?, note = ?
        WHERE id = ?
        """,
        (
            contact["name"], contact["contact"], contact["company"], contact["phone"], contact["email"],
            contact["country"], contact["interested_product"], contact["attachment_url"],
            contact["message"], contact["status"], contact["is_read"], contact["note"], contact_id,
        ),
    )


def delete_contact_record(contact_id):
    execute_write("DELETE FROM contact_requests WHERE id = ?", (contact_id,))


def list_all_contacts():
    return query_all(
        """
        SELECT id, name, contact, company, phone, email, country, interested_product, attachment_url, message, status, is_read, note, created_at
        FROM contact_requests
        ORDER BY created_at DESC, id DESC
        """
    )
