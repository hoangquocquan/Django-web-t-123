"""Read-only repository adapter for quotation requests."""

from django.db.models import Prefetch

from apps.sales.models import QuoteFile, QuoteRequest, QuoteRequestItem
from apps.sales.repositories.base import LegacySalesRepository


class QuotationRepository(LegacySalesRepository):
    """Read quotation headers, items and files from the legacy database."""

    model = QuoteRequest

    def list_quotes(self):
        """Return quote headers joined with customer to avoid N+1 queries."""
        return self.queryset().select_related("customer").all()

    def list_quotes_with_details(self):
        """Return quote headers and preload items/files for list or report views."""
        return self.list_quotes().prefetch_related(
            Prefetch("items", queryset=self.quote_item_queryset()),
            Prefetch("files", queryset=self.quote_file_queryset()),
        )

    def get_quote(self, quote_id):
        """Return one quotation request by legacy ID."""
        return self.list_quotes().get(id=quote_id)

    def get_quote_with_details(self, quote_id):
        """Return one quotation request with items and files preloaded."""
        return self.list_quotes_with_details().get(id=quote_id)

    def quote_item_queryset(self):
        """Create the base item QuerySet on the legacy database."""
        return (
            QuoteRequestItem.objects.using(self.database_alias)
            .select_related("product", "material")
            .all()
        )

    def list_quote_items(self, quote_id):
        """Return items that belong to one quotation request."""
        return self.quote_item_queryset().filter(quote_request_id=quote_id)

    def quote_file_queryset(self):
        """Create the base quote file QuerySet on the legacy database."""
        return QuoteFile.objects.using(self.database_alias).all()

    def list_quote_files(self, quote_id):
        """Return files that belong to one quotation request."""
        return self.quote_file_queryset().filter(quote_request_id=quote_id)
