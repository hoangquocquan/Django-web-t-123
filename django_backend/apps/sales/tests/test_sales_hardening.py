"""Hardening tests for Phase 6.1 sales quotation governance."""

from django.db import connections

from apps.sales.models import QuoteFile, QuoteRequest, QuoteRequestItem
from apps.sales.repositories.quotation_repository import QuotationRepository


def test_quote_requests_do_not_have_missing_customer_references(legacy_db):
    """Every quote request must point to an existing customer."""
    with connections["legacy"].cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM quote_requests quotes
            LEFT JOIN customers customers ON customers.id = quotes.customer_id
            WHERE customers.id IS NULL
            """
        )
        missing_customer_count = cursor.fetchone()[0]

    assert missing_customer_count == 0


def test_quote_items_do_not_have_missing_product_or_material_references(legacy_db):
    """Optional product/material references must be valid when present."""
    with connections["legacy"].cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM quote_request_items items
            LEFT JOIN products products ON products.id = items.product_id
            WHERE items.product_id IS NOT NULL AND products.id IS NULL
            """
        )
        missing_product_count = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM quote_request_items items
            LEFT JOIN materials materials ON materials.id = items.material_id
            WHERE items.material_id IS NOT NULL AND materials.id IS NULL
            """
        )
        missing_material_count = cursor.fetchone()[0]

    assert missing_product_count == 0
    assert missing_material_count == 0


def test_quote_items_have_positive_quantities(legacy_db):
    """Quantity must be positive for current legacy quote items."""
    bad_items = QuoteRequestItem.objects.using("legacy").filter(quantity__lte=0)

    assert bad_items.count() == 0


def test_quote_files_have_required_metadata_and_parent_quote(legacy_db):
    """Quote files must keep file name, file URL and parent quote relationship."""
    file_record = QuoteFile.objects.using("legacy").select_related("quote_request").first()

    assert file_record is not None
    assert file_record.quote_request.id == file_record.quote_request_id
    assert file_record.file_name
    assert file_record.file_url


def test_sales_repository_detail_querysets_use_legacy_alias(legacy_db):
    """Repository detail querysets must stay on the legacy database alias."""
    repository = QuotationRepository()
    quote = QuoteRequest.objects.using("legacy").first()

    assert repository.list_quote_items(quote.id)._db == "legacy"
    assert repository.list_quote_files(quote.id)._db == "legacy"


def test_sales_legacy_db_fixture_uses_database_copy(legacy_db):
    """Sales tests must use the copied test database, not the source SQLite file."""
    normalized_path = legacy_db.as_posix()

    assert normalized_path.endswith("mecprecision-test.sqlite")
    assert "/backend/database/" not in normalized_path
