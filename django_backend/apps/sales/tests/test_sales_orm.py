"""Validation tests for Phase 6 read-only quotation ORM mappings."""

from django.db import connections
import pytest

from apps.sales.models import QuoteFile, QuoteRequest, QuoteRequestItem
from apps.sales.repositories.quotation_repository import QuotationRepository
from apps.sales.services.quotation_service import QuotationService


def table_count(table_name):
    """Count rows directly in a legacy table for ORM parity checks."""
    with connections["legacy"].cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]


def test_quote_request_model_table_mapping_matches_legacy_count(legacy_db):
    """QuoteRequest model maps to the existing `quote_requests` table."""
    assert QuoteRequest.objects.using("legacy").count() == table_count("quote_requests")


def test_quote_item_model_table_mapping_matches_legacy_count(legacy_db):
    """QuoteRequestItem model maps to the existing `quote_request_items` table."""
    assert QuoteRequestItem.objects.using("legacy").count() == table_count("quote_request_items")


def test_quote_file_model_table_mapping_matches_legacy_count(legacy_db):
    """QuoteFile model maps to the existing `quote_files` table."""
    assert QuoteFile.objects.using("legacy").count() == table_count("quote_files")


def test_quote_header_customer_relationship_resolves(legacy_db):
    """QuoteRequest -> Customer foreign key resolves through the legacy alias."""
    quote = QuoteRequest.objects.using("legacy").select_related("customer").first()

    assert quote is not None
    assert quote.customer_id == quote.customer.id
    assert quote.customer.contact_name


def test_quote_item_relationships_resolve(legacy_db):
    """Quote items can access quote header and optional product/material references."""
    item = (
        QuoteRequestItem.objects.using("legacy")
        .select_related("quote_request", "product", "material")
        .first()
    )

    assert item is not None
    assert item.quote_request_id == item.quote_request.id
    if item.product_id:
        assert item.product.id == item.product_id
    if item.material_id:
        assert item.material.id == item.material_id


def test_quote_file_path_preservation(legacy_db):
    """Quote file mapping must preserve the original file URL/path exactly."""
    file_record = QuoteFile.objects.using("legacy").first()

    assert file_record is not None
    with connections["legacy"].cursor() as cursor:
        cursor.execute("SELECT file_url FROM quote_files WHERE id = ?", (file_record.id,))
        direct_file_url = cursor.fetchone()[0]

    assert file_record.file_url == direct_file_url


def test_sales_models_block_instance_save_and_delete(legacy_db):
    """Sales legacy models reject accidental instance writes."""
    quote = QuoteRequest.objects.using("legacy").first()

    with pytest.raises(RuntimeError):
        quote.save()

    with pytest.raises(RuntimeError):
        quote.delete()


def test_sales_models_block_bulk_update_and_delete(legacy_db):
    """Sales legacy querysets reject accidental bulk writes."""
    queryset = QuoteRequest.objects.using("legacy").filter(status="new")

    with pytest.raises(RuntimeError):
        queryset.update(status="done")

    with pytest.raises(RuntimeError):
        queryset.delete()


def test_quotation_repository_reads_from_legacy_database(legacy_db):
    """QuotationRepository must create QuerySets on alias `legacy`."""
    repository = QuotationRepository()
    queryset = repository.list_quotes()

    assert queryset._db == "legacy"
    assert list(queryset)


def test_quotation_service_uses_repository_for_quote_detail(legacy_db):
    """QuotationService returns quote detail through repository calls."""
    quote = QuoteRequest.objects.using("legacy").first()
    service = QuotationService()

    detail = service.get_quote_detail(quote.id)

    assert detail["quote"].id == quote.id
    assert "items" in detail
    assert "files" in detail


def test_quotation_service_can_use_repository_double_without_orm():
    """Service can be tested without ORM because it depends on repository interface."""

    class FakeQuotationRepository:
        """Repository double for service behavior tests."""

        def list_quotes(self):
            return ["quote-a"]

        def get_quote(self, quote_id):
            return {"id": quote_id}

        def list_quote_items(self, quote_id):
            return [f"item-{quote_id}"]

        def list_quote_files(self, quote_id):
            return [f"file-{quote_id}"]

    service = QuotationService(quotation_repository=FakeQuotationRepository())

    assert service.list_quotes() == ["quote-a"]
    assert service.get_quote_detail(5) == {
        "quote": {"id": 5},
        "items": ["item-5"],
        "files": ["file-5"],
    }
