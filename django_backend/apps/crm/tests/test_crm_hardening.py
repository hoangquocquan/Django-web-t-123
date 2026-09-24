"""Hardening tests for Phase 5.1 CRM migration governance."""

from django.db import connections

from apps.crm.models import ContactRequest, Customer
from apps.crm.repositories.contact_repository import ContactRequestRepository
from apps.crm.repositories.customer_repository import CustomerRepository


def test_customer_notes_do_not_have_orphan_rows(legacy_db):
    """customer_notes must not point to missing customers."""
    with connections["legacy"].cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM customer_notes notes
            LEFT JOIN customers customers ON customers.id = notes.customer_id
            WHERE customers.id IS NULL
            """
        )
        orphan_count = cursor.fetchone()[0]

    assert orphan_count == 0


def test_contact_request_has_no_customer_relationship_field(legacy_db):
    """ContactRequest mirrors the legacy schema and does not invent customer_id."""
    field_names = {field.name for field in ContactRequest._meta.fields}

    assert "customer" not in field_names
    assert "customer_id" not in field_names


def test_crm_repository_get_methods_return_legacy_records(legacy_db):
    """Repository get methods must resolve records through the legacy database."""
    customer = Customer.objects.using("legacy").first()
    contact = ContactRequest.objects.using("legacy").first()

    assert CustomerRepository().get_customer(customer.id).id == customer.id
    assert ContactRequestRepository().get_contact(contact.id).id == contact.id


def test_legacy_db_fixture_uses_database_copy(legacy_db):
    """CRM tests must use the copied fixture database, not the source database."""
    normalized_path = legacy_db.as_posix()

    assert normalized_path.endswith("mecprecision-test.sqlite")
    assert "/backend/database/" not in normalized_path


def test_customer_repository_prefetches_notes_on_legacy_alias(legacy_db):
    """Customer notes relationship should be loaded through the legacy alias."""
    queryset = CustomerRepository().list_customers_with_notes()
    customers = list(queryset)

    assert queryset._db == "legacy"
    assert customers
    assert all(customer.notes.all()._db == "legacy" for customer in customers)
