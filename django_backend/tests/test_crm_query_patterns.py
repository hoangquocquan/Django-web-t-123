"""Test query pattern CRM để Phase 5 làm mẫu cho module sau."""

from apps.crm.repositories.contact_repository import ContactRequestRepository
from apps.crm.repositories.customer_repository import CustomerRepository


def test_customer_list_uses_single_query(legacy_db, django_assert_num_queries):
    """Danh sách khách hàng chưa cần relationship nên chỉ dùng một query."""
    repository = CustomerRepository()

    with django_assert_num_queries(1, using="legacy"):
        customers = list(repository.list_customers())

    assert customers


def test_customer_list_with_notes_prefetches_notes(legacy_db, django_assert_num_queries):
    """Danh sách khách hàng kèm ghi chú dùng prefetch để tránh N+1 queries."""
    repository = CustomerRepository()

    with django_assert_num_queries(2, using="legacy"):
        customers = list(repository.list_customers_with_notes())
        note_groups = [list(customer.notes.all()) for customer in customers]

    assert customers
    assert len(note_groups) == len(customers)


def test_recent_contacts_uses_single_query(legacy_db, django_assert_num_queries):
    """Danh sách liên hệ mới nhất chỉ cần một query."""
    repository = ContactRequestRepository()

    with django_assert_num_queries(1, using="legacy"):
        contacts = list(repository.list_recent_contacts(limit=5))

    assert contacts
