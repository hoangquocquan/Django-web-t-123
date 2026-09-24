"""Import legacy newsletter subscribers into the Django-owned table."""

from __future__ import annotations

import sqlite3
from urllib.parse import unquote, urlparse

from django.conf import settings
from django.db import migrations
from django.utils import timezone
from django.utils.dateparse import parse_datetime


def legacy_sqlite_name():
    """Return the configured legacy SQLite database URI or path."""
    legacy_config = settings.DATABASES.get("legacy", {})
    return str(legacy_config.get("NAME", ""))


def parse_legacy_datetime(value):
    """Convert legacy text timestamps into timezone-aware datetimes."""
    if not value:
        return None
    parsed = parse_datetime(str(value))
    if parsed is None:
        parsed = parse_datetime(str(value).replace(" ", "T"))
    if parsed is None:
        return timezone.now()
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def import_legacy_subscribers(apps, schema_editor):
    """Copy subscribers from read-only legacy SQLite into Django default DB."""
    if schema_editor.connection.alias != "default":
        return

    database_name = legacy_sqlite_name()
    if not database_name:
        return

    parsed = urlparse(database_name)
    if parsed.scheme == "file":
        legacy_path = unquote(parsed.path)
        if parsed.netloc:
            legacy_path = f"//{parsed.netloc}{legacy_path}"
        connection_name = database_name
        use_uri = True
    else:
        legacy_path = database_name
        connection_name = database_name
        use_uri = False

    if not legacy_path:
        return

    NewsletterSubscriber = apps.get_model("newsletter", "NewsletterSubscriber")
    try:
        legacy_connection = sqlite3.connect(connection_name, uri=use_uri)
    except sqlite3.Error:
        return

    try:
        legacy_connection.row_factory = sqlite3.Row
        rows = legacy_connection.execute(
            """
            SELECT id, email, status, subscribed_at, unsubscribed_at
            FROM newsletter_subscribers
            ORDER BY id
            """
        ).fetchall()
    except sqlite3.Error:
        rows = []
    finally:
        legacy_connection.close()

    for row in rows:
        if not row["email"]:
            continue
        NewsletterSubscriber.objects.update_or_create(
            email=row["email"],
            defaults={
                "id": row["id"],
                "status": row["status"] or "subscribed",
                "source": "legacy_import",
                "subscribed_at": parse_legacy_datetime(row["subscribed_at"]) or timezone.now(),
                "unsubscribed_at": parse_legacy_datetime(row["unsubscribed_at"]),
            },
        )


def noop_reverse(apps, schema_editor):
    """Do not delete imported subscribers on reverse migration."""
    return


class Migration(migrations.Migration):

    dependencies = [
        ("newsletter", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(import_legacy_subscribers, noop_reverse),
    ]
