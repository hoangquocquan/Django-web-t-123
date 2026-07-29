# Wave 6 Django Admin UI Review

## Decision

`PASS_WITH_WARNING`

## Reason

Wave 6 successfully introduces a Django-owned browser admin UI for migrated modules, but legacy admin must remain because several CMS and tooling screens are still not migrated.

## Security Review

- CSRF protection is active.
- Browser login uses Foundation authentication.
- Session stores a Foundation token, not raw credentials.
- Write forms require Foundation module permissions.
- Django technical admin remains separate at `/django-admin/`.

## API / UI Impact

- `/admin/` now routes to the MEC Django admin UI inside the Django backend.
- Django built-in technical admin moved to `/django-admin/`.
- `/api/v1/admin/` remains available from Wave 5.

## Database Impact

No new database tables or migrations were introduced.

## Warning

This is a UI cutover for migrated domains only. It is not authorization to delete the legacy admin or shut down production routes.
