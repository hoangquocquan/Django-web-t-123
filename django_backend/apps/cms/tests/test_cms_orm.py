"""Validation tests for Phase 7 read-only CMS ORM mappings."""

from django.db import connections
import pytest

from apps.cms.models import CmsBanner, CmsMenuItem, CmsPage, NewsletterSubscriber
from apps.cms.repositories.banner_repository import CmsBannerRepository
from apps.cms.repositories.menu_repository import CmsMenuRepository
from apps.cms.repositories.newsletter_repository import NewsletterRepository
from apps.cms.repositories.page_repository import CmsPageRepository
from apps.cms.services.cms_service import CmsService


def table_count(table_name):
    """Count rows directly in a legacy table for ORM parity checks."""
    with connections["legacy"].cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]


def test_cms_page_model_table_mapping_matches_legacy_count(legacy_db):
    """CmsPage model maps to `cms_pages`."""
    assert CmsPage.objects.using("legacy").count() == table_count("cms_pages")


def test_cms_menu_model_table_mapping_matches_legacy_count(legacy_db):
    """CmsMenuItem model maps to `cms_menu_items`."""
    assert CmsMenuItem.objects.using("legacy").count() == table_count("cms_menu_items")


def test_cms_banner_model_table_mapping_matches_legacy_count(legacy_db):
    """CmsBanner model maps to `cms_banners`, even when the table is empty."""
    assert CmsBanner.objects.using("legacy").count() == table_count("cms_banners")


def test_newsletter_model_table_mapping_matches_legacy_count(legacy_db):
    """NewsletterSubscriber model maps to `newsletter_subscribers`."""
    assert NewsletterSubscriber.objects.using("legacy").count() == table_count(
        "newsletter_subscribers"
    )


def test_menu_self_referential_relationship_is_available(legacy_db):
    """Menu item self-reference is mapped through parent and children."""
    menu_item = CmsMenuItem.objects.using("legacy").first()

    assert menu_item is not None
    assert hasattr(menu_item, "children")
    assert CmsMenuItem._meta.get_field("parent").remote_field.model is CmsMenuItem


def test_menu_items_do_not_have_orphan_parent_references(legacy_db):
    """Nested menu parent references must point to existing menu items."""
    with connections["legacy"].cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM cms_menu_items child
            LEFT JOIN cms_menu_items parent ON parent.id = child.parent_id
            WHERE child.parent_id IS NOT NULL AND parent.id IS NULL
            """
        )
        orphan_count = cursor.fetchone()[0]

    assert orphan_count == 0


def test_cms_models_block_instance_save_and_delete(legacy_db):
    """CMS legacy models reject accidental instance writes."""
    page = CmsPage.objects.using("legacy").first()

    with pytest.raises(RuntimeError):
        page.save()

    with pytest.raises(RuntimeError):
        page.delete()


def test_cms_models_block_bulk_update_and_delete(legacy_db):
    """CMS legacy querysets reject accidental bulk writes."""
    queryset = CmsPage.objects.using("legacy").filter(status="published")

    with pytest.raises(RuntimeError):
        queryset.update(status="draft")

    with pytest.raises(RuntimeError):
        queryset.delete()


def test_cms_repositories_read_from_legacy_database(legacy_db):
    """CMS repositories must create QuerySets on alias `legacy`."""
    assert CmsPageRepository().list_pages()._db == "legacy"
    assert CmsMenuRepository().list_menu_items()._db == "legacy"
    assert CmsBannerRepository().list_banners()._db == "legacy"
    assert NewsletterRepository().list_subscribers()._db == "legacy"


def test_cms_service_uses_repositories_for_public_content(legacy_db):
    """CmsService exposes read-only content through repositories."""
    page = CmsPage.objects.using("legacy").filter(status="published").first()
    service = CmsService()

    assert service.get_public_page(page.slug).id == page.id
    assert list(service.list_public_pages())
    assert list(service.list_navigation("header"))
    assert list(service.list_newsletter_subscribers())


def test_cms_service_can_use_repository_doubles_without_orm():
    """Service can be tested without ORM because it depends on repository interfaces."""

    class FakePageRepository:
        def list_published_pages(self):
            return ["page-a"]

        def get_published_page_by_slug(self, slug):
            return {"slug": slug}

    class FakeMenuRepository:
        def list_root_menu_items(self, location=None):
            return [f"menu-{location}"]

    class FakeBannerRepository:
        def list_active_banners(self, placement):
            return [f"banner-{placement}"]

    class FakeNewsletterRepository:
        def list_subscribers(self):
            return ["subscriber-a"]

    service = CmsService(
        page_repository=FakePageRepository(),
        menu_repository=FakeMenuRepository(),
        banner_repository=FakeBannerRepository(),
        newsletter_repository=FakeNewsletterRepository(),
    )

    assert service.list_public_pages() == ["page-a"]
    assert service.get_public_page("about") == {"slug": "about"}
    assert service.list_navigation("header") == ["menu-header"]
    assert service.list_active_banners("home_slider") == ["banner-home_slider"]
    assert service.list_newsletter_subscribers() == ["subscriber-a"]
