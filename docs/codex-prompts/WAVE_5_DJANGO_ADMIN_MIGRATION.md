# Wave 5 - Django Admin Interface Migration

## Objective

Move admin interface ownership for migrated Django domains from the legacy custom HTTP server to Django REST Framework while preserving legacy compatibility.

## Scope

- Admin authentication endpoint.
- Admin dashboard metrics.
- Admin navigation metadata.
- Role-based admin access.
- Admin operations for products, customers, inventory, orders, workflows, transaction history, and permissions.

## DO NOT

- Do not delete or disable legacy admin pages.
- Do not change production routing.
- Do not migrate unrelated CMS modules.
- Do not remove legacy database tables.
- Do not bypass human approval.

## Implementation Tasks

1. Audit current legacy admin routes and service dependencies.
2. Add Django-owned admin serializers and API views.
3. Reuse Django foundation authentication and permission services.
4. Reuse Django business and transaction domain services.
5. Add tests for login, dashboard, permissions, CRUD-like admin operations, inventory, orders, workflows, and legacy compatibility.
6. Create evidence and review reports.

## Testing Requirements

- `python manage.py check`
- `pytest tests/test_wave5_admin_migration.py`
- `pytest`
- `python ai-factory/run_ai_factory.py --wave django-wave-5`

## Git Requirements

- Branch: `feature/wave-5-django-admin-migration`
- Commit: `feat: migrate admin interface ownership to django`
- Tag: `wave-5-django-admin-complete`

## Expected Output

Final status: `DJANGO_ADMIN_MIGRATION_COMPLETE`.
