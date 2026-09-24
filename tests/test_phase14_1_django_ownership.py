import sqlite3

import pytest
from django.db import connection

from apps.catalog.models import Product
from apps.cms.models import CmsPage, NewsletterSubscriber as LegacyNewsletterSubscriber
from apps.cms.repositories.newsletter_repository import NewsletterRepository
from apps.newsletter.models import NewsletterSubscriber
from apps.newsletter.services import NewsletterService
from tests.legacy_sqlite_helpers import create_legacy_sqlite_fixture


@pytest.fixture
def legacy_db(tmp_path):
    """Return a read-only copied legacy SQLite database path."""
    return create_legacy_sqlite_fixture(
        tmp_path / "legacy_database" / "mecprecision-test.sqlite"
    )


def count_legacy_rows(legacy_db, table_name):
    """Count rows in the copied legacy database without using Django alias."""
    connection_uri = f"file:{legacy_db.as_posix()}?mode=ro"
    with sqlite3.connect(connection_uri, uri=True) as legacy_connection:
        return legacy_connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]


@pytest.mark.django_db
def test_django_owned_newsletter_model_works():
    subscriber = NewsletterSubscriber.objects.create(
        email="phase14-1@example.com",
        source="phase14-test",
    )

    assert subscriber.id
    assert subscriber.status == "subscribed"
    assert NewsletterSubscriber._meta.managed is True


@pytest.mark.django_db
def test_newsletter_migration_created_default_table():
    table_names = connection.introspection.table_names()

    assert "newsletter_subscribers" in table_names


@pytest.mark.django_db
def test_newsletter_service_subscribe_is_idempotent():
    service = NewsletterService()

    subscriber, created = service.subscribe("idempotent@example.com", source="unit-test")
    same_subscriber, created_again = service.subscribe("idempotent@example.com", source="unit-test")

    assert created is True
    assert created_again is False
    assert same_subscriber.id == subscriber.id
    assert NewsletterSubscriber.objects.filter(email="idempotent@example.com").count() == 1


@pytest.mark.django_db
def test_newsletter_api_write_uses_django_model(client):
    response = client.post(
        "/api/v1/newsletter/subscribers/",
        data={"email": "api-owner@example.com", "source": "api-test"},
        content_type="application/json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["created"] is True
    assert body["data"]["email"] == "api-owner@example.com"
    assert NewsletterSubscriber.objects.filter(email="api-owner@example.com").exists()


@pytest.mark.django_db
def test_newsletter_api_duplicate_preserves_compatibility(client):
    NewsletterSubscriber.objects.create(email="duplicate@example.com", source="seed")

    response = client.post(
        "/api/v1/newsletter/subscribers/",
        data={"email": "duplicate@example.com", "source": "api-test"},
        content_type="application/json",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["created"] is False
    assert body["data"]["email"] == "duplicate@example.com"


@pytest.mark.django_db
def test_newsletter_api_list_reads_django_owned_records(client):
    NewsletterSubscriber.objects.create(email="list-owner@example.com", source="api-test")

    response = client.get("/api/v1/newsletter/subscribers/")

    assert response.status_code == 200
    body = response.json()
    emails = [item["email"] for item in body["data"]["results"]]
    assert "list-owner@example.com" in emails


@pytest.mark.django_db
def test_legacy_newsletter_compatibility_remains_read_only(legacy_db):
    assert LegacyNewsletterSubscriber._meta.managed is False
    assert NewsletterRepository().list_subscribers()._db == "legacy"
    assert count_legacy_rows(legacy_db, "newsletter_subscribers") >= 1

    legacy_subscriber = LegacyNewsletterSubscriber(
        id=1,
        email="legacy@example.com",
        status="subscribed",
        subscribed_at="2026-01-01 00:00:00",
    )
    with pytest.raises(RuntimeError):
        legacy_subscriber.save()


@pytest.mark.django_db
def test_no_unrelated_domain_ownership_changed(legacy_db):
    assert CmsPage._meta.managed is False
    assert Product._meta.managed is False
    assert count_legacy_rows(legacy_db, "products") >= 1
