# CMS Migration Limitations

## Scope In Phase 7

Phase 7 only implements the CMS/content read-only ORM slice in Django.

Mapped tables:

- `cms_pages`
- `cms_menu_items`
- `cms_banners`
- `newsletter_subscribers`

## What Is Intentionally Not Included

- No CMS write CRUD.
- No serializer.
- No API endpoint.
- No admin UI behavior change.
- No upload migration.
- No authentication migration.
- No page/menu/banner/newsletter table modification.

## Menu Relationship Boundary

`cms_menu_items.parent_id` is a self-referential foreign key.

Django maps it as:

```python
CmsMenuItem.parent
CmsMenuItem.children
```

Current demo data has no nested menu rows, but the relationship is mapped and orphan parent references are tested.

## Banner Data Boundary

`cms_banners` currently has 0 rows in the demo database.

Phase 7 validates table mapping and repository behavior, but cannot validate real banner content until data exists.

## Newsletter Boundary

`newsletter_subscribers` is mapped read-only for future export and CMS read views.

Subscribe/unsubscribe write behavior remains legacy-only until a future approved migration phase.

## Future Readiness

Phase 7 prepares future CMS migration work for:

- public page read API,
- navigation/menu read API,
- banner read API,
- newsletter export,
- CMS write migration after auth boundary is approved.
