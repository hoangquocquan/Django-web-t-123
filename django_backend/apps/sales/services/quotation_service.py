"""Read-only quotation service layer."""

from apps.sales.repositories.quotation_repository import QuotationRepository


class QuotationService:
    """Service for read-only quotation workflows."""

    def __init__(self, quotation_repository=None):
        """Allow tests to pass a repository double without touching the ORM."""
        self.quotation_repository = quotation_repository or QuotationRepository()

    def list_quotes(self):
        """Return quote requests with customer data."""
        return self.quotation_repository.list_quotes()

    def get_quote_detail(self, quote_id):
        """Return one quote request with its line items and uploaded files."""
        quote = self.quotation_repository.get_quote(quote_id)
        items = self.quotation_repository.list_quote_items(quote_id)
        files = self.quotation_repository.list_quote_files(quote_id)
        return {
            "quote": quote,
            "items": items,
            "files": files,
        }

    def list_quote_files(self, quote_id):
        """Return uploaded files for one quote without changing file metadata."""
        return self.quotation_repository.list_quote_files(quote_id)
