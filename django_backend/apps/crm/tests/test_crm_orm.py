"""Validation tests for Phase 5 read-only CRM ORM mappings."""

from django.db import connections
import pytest

from apps.crm.models import ContactRequest, Customer, CustomerNote
from apps.crm.repositories.contact_repository import ContactRequestRepository
from apps.crm.repositories.customer_repository import CustomerRepository
from apps.crm.services.crm_service import CrmService


def table_count(table_name):
    """Đếm trực tiếp số dòng trong một bảng legacy để so với ORM."""
    with connections["legacy"].cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]


def test_customer_model_table_mapping_matches_legacy_count(legacy_db):
    """Customer model phải map đúng bảng `customers`."""
    assert Customer.objects.using("legacy").count() == table_count("customers")


def test_contact_request_model_table_mapping_matches_legacy_count(legacy_db):
    """ContactRequest model phải map đúng bảng `contact_requests`."""
    assert ContactRequest.objects.using("legacy").count() == table_count("contact_requests")


def test_customer_note_model_table_mapping_matches_legacy_count(legacy_db):
    """CustomerNote model phải map đúng bảng `customer_notes`, kể cả khi bảng đang rỗng."""
    assert CustomerNote.objects.using("legacy").count() == table_count("customer_notes")


def test_customer_notes_relationship_is_available(legacy_db):
    """Quan hệ Customer -> CustomerNote phải truy cập được qua related_name `notes`."""
    customer = Customer.objects.using("legacy").prefetch_related("notes").first()

    assert customer is not None
    assert list(customer.notes.all()) == list(
        CustomerNote.objects.using("legacy").filter(customer_id=customer.id)
    )


def test_crm_models_block_instance_save_and_delete(legacy_db):
    """CRM legacy model phải chặn ghi dữ liệu qua instance."""
    customer = Customer.objects.using("legacy").first()

    with pytest.raises(RuntimeError):
        customer.save()

    with pytest.raises(RuntimeError):
        customer.delete()


def test_crm_models_block_bulk_update_and_delete(legacy_db):
    """CRM legacy queryset phải chặn bulk update/delete."""
    queryset = ContactRequest.objects.using("legacy").filter(status="new")

    with pytest.raises(RuntimeError):
        queryset.update(status="done")

    with pytest.raises(RuntimeError):
        queryset.delete()


def test_customer_repository_reads_from_legacy_database(legacy_db):
    """CustomerRepository phải tạo QuerySet trên alias `legacy`."""
    queryset = CustomerRepository().list_customers()

    assert queryset._db == "legacy"
    assert list(queryset)


def test_contact_repository_reads_from_legacy_database(legacy_db):
    """ContactRequestRepository phải tạo QuerySet trên alias `legacy`."""
    queryset = ContactRequestRepository().list_contacts()

    assert queryset._db == "legacy"
    assert list(queryset)


def test_crm_service_uses_repository_for_customer_profile(legacy_db):
    """CrmService lấy customer profile thông qua repository."""
    customer = Customer.objects.using("legacy").first()
    service = CrmService()

    profile = service.get_customer_profile(customer.id)

    assert profile["customer"].id == customer.id
    assert "notes" in profile


def test_crm_service_can_use_repository_doubles_without_orm():
    """Service dễ test độc lập vì chỉ phụ thuộc interface repository."""

    class FakeCustomerRepository:
        """Repository giả cho luồng customer."""

        def list_customers_with_notes(self):
            return ["customer-a"]

        def get_customer(self, customer_id):
            return {"id": customer_id}

        def list_customer_notes(self, customer_id):
            return [f"note-for-{customer_id}"]

    class FakeContactRepository:
        """Repository giả cho luồng contact."""

        def list_recent_contacts(self, limit=10):
            return [f"contact-{limit}"]

        def get_contact(self, contact_id):
            return {"id": contact_id}

    service = CrmService(
        customer_repository=FakeCustomerRepository(),
        contact_repository=FakeContactRepository(),
    )

    assert service.list_customer_profiles() == ["customer-a"]
    assert service.get_customer_profile(7) == {
        "customer": {"id": 7},
        "notes": ["note-for-7"],
    }
    assert service.list_recent_contacts(limit=3) == ["contact-3"]
    assert service.get_contact(9) == {"id": 9}
