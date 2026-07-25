"""Read-only CRM service layer."""

from apps.crm.repositories.contact_repository import ContactRequestRepository
from apps.crm.repositories.customer_repository import CustomerRepository


class CrmService:
    """Service CRM chỉ đọc, phụ thuộc repository thay vì gọi ORM trực tiếp."""

    def __init__(self, customer_repository=None, contact_repository=None):
        """Cho phép test truyền repository giả để kiểm tra service độc lập."""
        self.customer_repository = customer_repository or CustomerRepository()
        self.contact_repository = contact_repository or ContactRequestRepository()

    def list_customer_profiles(self):
        """Trả về khách hàng kèm ghi chú đã preload."""
        return self.customer_repository.list_customers_with_notes()

    def get_customer_profile(self, customer_id):
        """Trả về một khách hàng và danh sách ghi chú liên quan."""
        customer = self.customer_repository.get_customer(customer_id)
        notes = self.customer_repository.list_customer_notes(customer_id)
        return {
            "customer": customer,
            "notes": notes,
        }

    def list_recent_contacts(self, limit=10):
        """Trả về danh sách liên hệ mới nhất."""
        return self.contact_repository.list_recent_contacts(limit=limit)

    def get_contact(self, contact_id):
        """Trả về một liên hệ theo ID."""
        return self.contact_repository.get_contact(contact_id)
