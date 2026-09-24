# Wave 6 - Django Admin UI Cutover

## Objective

Move browser-facing admin UI ownership from legacy HTML admin to Django while preserving rollback compatibility.

## Scope

- Django admin UI app.
- Admin layout and navigation.
- Browser login/logout backed by Foundation authentication.
- Permission-filtered menu and write protection.
- Dashboard, products, customers, inventory, orders, workflows, and transaction history screens.

## DO NOT

- Do not delete legacy admin files.
- Do not shut down production.
- Do not migrate the public website.
- Do not call legacy `backend/services` or `backend/repositories`.
- Do not bypass CSRF or permission checks.

## Implementation Tasks

1. Audit legacy browser admin UI.
2. Create Django admin UI foundation.
3. Render migrated domain screens from Django templates.
4. Submit writes to Django-owned services.
5. Preserve rollback path and Django technical admin.
6. Add tests and AI Factory evidence.

## Testing Requirements

- `python manage.py check`
- `pytest tests/test_wave6_admin_ui.py`
- `pytest`
- `python ai-factory/run_ai_factory.py --wave django-wave-6`

## Git Requirements

- Branch: `feature/wave-6-django-admin-ui-cutover`
- Commit: `feat: migrate admin ui ownership to django`
- Tag: `wave-6-admin-ui-complete`

## Expected Output

Final status: `DJANGO_ADMIN_UI_CUTOVER_COMPLETE`.
