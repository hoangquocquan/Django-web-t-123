"""Query pattern tests for sales/quotation repositories."""

from apps.sales.repositories.quotation_repository import QuotationRepository


def test_quote_list_selects_customer_in_one_query(legacy_db, django_assert_num_queries):
    """Quote list should load customer data in a single query."""
    repository = QuotationRepository()

    with django_assert_num_queries(1, using="legacy"):
        quotes = list(repository.list_quotes())
        customer_names = [quote.customer.contact_name for quote in quotes]

    assert quotes
    assert all(customer_names)


def test_quote_list_with_details_prefetches_items_and_files(
    legacy_db,
    django_assert_num_queries,
):
    """Quote list with details should preload items and files with stable query count."""
    repository = QuotationRepository()

    with django_assert_num_queries(3, using="legacy"):
        quotes = list(repository.list_quotes_with_details())
        item_groups = [list(quote.items.all()) for quote in quotes]
        file_groups = [list(quote.files.all()) for quote in quotes]

    assert quotes
    assert len(item_groups) == len(quotes)
    assert len(file_groups) == len(quotes)


def test_quote_detail_service_has_stable_query_count(legacy_db, django_assert_num_queries):
    """Current quote detail service uses one query each for header, items and files."""
    repository = QuotationRepository()
    quote = repository.list_quotes().first()

    with django_assert_num_queries(3, using="legacy"):
        detail = repository.get_quote_with_details(quote.id)
        items = list(detail.items.all())
        files = list(detail.files.all())

    assert detail.id == quote.id
    assert isinstance(items, list)
    assert isinstance(files, list)
