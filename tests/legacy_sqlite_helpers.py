"""Deterministic temporary legacy SQLite fixture for compatibility tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA = (
    "CREATE TABLE admin_users (id INTEGER PRIMARY KEY, email TEXT NOT NULL)",
    "CREATE TABLE product_categories (id INTEGER PRIMARY KEY, name TEXT NOT NULL)",
    "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, category_id INTEGER)",
    "CREATE TABLE customers (id INTEGER PRIMARY KEY, company_name TEXT NOT NULL)",
    "CREATE TABLE quote_requests (id INTEGER PRIMARY KEY, project_name TEXT NOT NULL, customer_id INTEGER)",
    "CREATE TABLE cms_pages (id INTEGER PRIMARY KEY, title TEXT NOT NULL, slug TEXT NOT NULL, status TEXT NOT NULL, sort_order INTEGER NOT NULL)",
    "CREATE TABLE admin_sessions (session_id TEXT PRIMARY KEY, expires_at TEXT NOT NULL)",
    "CREATE TABLE newsletter_subscribers (id INTEGER PRIMARY KEY, email TEXT NOT NULL)",
)

ROWS = (
    ("INSERT INTO admin_users (id, email) VALUES (?, ?)", (1, "legacy-admin@example.invalid")),
    ("INSERT INTO product_categories (id, name) VALUES (?, ?)", (1, "Legacy Category")),
    ("INSERT INTO products (id, name, category_id) VALUES (?, ?, ?)", (1, "Legacy Product", 1)),
    ("INSERT INTO customers (id, company_name) VALUES (?, ?)", (1, "Legacy Customer")),
    ("INSERT INTO quote_requests (id, project_name, customer_id) VALUES (?, ?, ?)", (1, "Legacy Quote", 1)),
    (
        "INSERT INTO cms_pages (id, title, slug, status, sort_order) VALUES (?, ?, ?, ?, ?)",
        (1, "Legacy Page", "legacy-page", "published", 1),
    ),
    (
        "INSERT INTO admin_sessions (session_id, expires_at) VALUES (?, ?)",
        ("legacy-session", "2099-01-01T00:00:00Z"),
    ),
    (
        "INSERT INTO newsletter_subscribers (id, email) VALUES (?, ?)",
        (1, "legacy-subscriber@example.invalid"),
    ),
)


def create_legacy_sqlite_fixture(path):
    """Create a disposable, minimal legacy-compatible SQLite database."""

    database_path = Path(path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        for statement in SCHEMA:
            connection.execute(statement)
        for statement, parameters in ROWS:
            connection.execute(statement, parameters)
        connection.commit()
    return database_path


def django_sqlite_database_config(path):
    """Return a fully normalized Django database alias for a SQLite fixture."""

    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(Path(path)),
        "ATOMIC_REQUESTS": False,
        "AUTOCOMMIT": True,
        "CONN_HEALTH_CHECKS": False,
        "CONN_MAX_AGE": 0,
        "OPTIONS": {},
        "TIME_ZONE": None,
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
        "TEST": {
            "CHARSET": None,
            "COLLATION": None,
            "MIGRATE": True,
            "MIRROR": None,
            "NAME": None,
        },
    }
