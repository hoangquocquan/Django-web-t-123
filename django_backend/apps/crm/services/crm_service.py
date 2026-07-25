"""Read-only CRM service layer."""

from apps.crm.repositories.contact_repository import ContactRequestRepository
from apps.crm.repositories.customer_repository import CustomerRepository


class CrmService:
    """Read-only CRM service that depends on repositories, not direct ORM."""

    def __init__(self, customer_repository=None, contact_repository=None):
        """Allow tests to pass repository doubles for isolated service checks."""
        self.customer_repository = customer_repository or CustomerRepository()
        self.contact_repository = contact_repository or ContactRequestRepository()

    def list_customer_profiles(self):
        """Return customers with notes preloaded by the repository."""
        return self.customer_repository.list_customers_with_notes()

    def get_customer_profile(self, customer_id):
        """Return one customer and the related care notes."""
        customer = self.customer_repository.get_customer(customer_id)
        notes = self.customer_repository.list_customer_notes(customer_id)
        return {
            "customer": customer,
            "notes": notes,
        }

    def list_recent_contacts(self, limit=10):
        """Return recent public contact requests."""
        return self.contact_repository.list_recent_contacts(limit=limit)

    def list_contact_requests(self):
        """Return all public contact requests through the repository boundary."""
        return self.contact_repository.list_contacts()

    def get_contact(self, contact_id):
        """Return one public contact request by ID."""
        return self.contact_repository.get_contact(contact_id)
