"""Read-only repository adapter for CRM customers."""

from django.db.models import Prefetch

from apps.crm.models import Customer, CustomerNote
from apps.crm.repositories.base import LegacyCrmRepository


class CustomerRepository(LegacyCrmRepository):
    """Đọc dữ liệu khách hàng từ legacy CRM database."""

    model = Customer

    def list_customers(self):
        """Trả về danh sách khách hàng."""
        return self.queryset().all()

    def list_customers_with_notes(self):
        """Trả về khách hàng và preload ghi chú để tránh N+1 queries."""
        return self.list_customers().prefetch_related(
            Prefetch("notes", queryset=self.customer_note_queryset())
        )

    def get_customer(self, customer_id):
        """Lấy một khách hàng theo legacy ID."""
        return self.queryset().get(id=customer_id)

    def customer_note_queryset(self):
        """Tạo QuerySet ghi chú khách hàng trên database legacy."""
        return CustomerNote.objects.using(self.database_alias)

    def list_customer_notes(self, customer_id):
        """Lấy ghi chú của một khách hàng."""
        return self.customer_note_queryset().filter(customer_id=customer_id)
