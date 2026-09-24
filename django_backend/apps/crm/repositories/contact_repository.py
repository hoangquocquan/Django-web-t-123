"""Read-only repository adapter for CRM contact requests."""

from apps.crm.models import ContactRequest
from apps.crm.repositories.base import LegacyCrmRepository


class ContactRequestRepository(LegacyCrmRepository):
    """Đọc dữ liệu form liên hệ từ legacy CRM database."""

    model = ContactRequest

    def list_contacts(self):
        """Trả về toàn bộ liên hệ theo thứ tự mới nhất."""
        return self.queryset().all()

    def list_recent_contacts(self, limit=10):
        """Trả về các liên hệ mới nhất để dashboard hoặc CRM dùng."""
        return self.list_contacts()[:limit]

    def list_contacts_by_status(self, status):
        """Lọc liên hệ theo trạng thái như new, processing, done."""
        return self.queryset().filter(status=status)

    def get_contact(self, contact_id):
        """Lấy một liên hệ theo legacy ID."""
        return self.queryset().get(id=contact_id)
