"""Query pattern tests for CMS repositories."""

from apps.cms.repositories.menu_repository import CmsMenuRepository
from apps.cms.repositories.page_repository import CmsPageRepository


def test_published_pages_use_single_query(legacy_db, django_assert_num_queries):
    """Published page list should use one legacy query."""
    repository = CmsPageRepository()

    with django_assert_num_queries(1, using="legacy"):
        pages = list(repository.list_published_pages())

    assert pages


def test_menu_items_select_parent_in_single_query(legacy_db, django_assert_num_queries):
    """Menu item list should load parent references in one query."""
    repository = CmsMenuRepository()

    with django_assert_num_queries(1, using="legacy"):
        menu_items = list(repository.list_menu_items())
        parent_ids = [item.parent.id for item in menu_items if item.parent_id]

    assert menu_items
    assert isinstance(parent_ids, list)


def test_root_menu_items_prefetch_children(legacy_db, django_assert_num_queries):
    """Root menu loading should prefetch children with stable query count."""
    repository = CmsMenuRepository()

    with django_assert_num_queries(2, using="legacy"):
        root_items = list(repository.list_root_menu_items(location="header"))
        child_groups = [list(item.children.all()) for item in root_items]

    assert root_items
    assert len(child_groups) == len(root_items)
