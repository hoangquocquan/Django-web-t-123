# Django Structure Audit

## Scope

Phase 14.0 inspected the current Django backend structure without modifying source code, database schema, or legacy files.

## Summary

The project has a real Django backend in `django_backend/`. It is not only a placeholder anymore: it contains settings, URL routing, Django REST Framework views, serializers, services, repositories, tests, and unmanaged ORM models for migrated business modules.

However, the Django backend still runs beside the legacy backend. Business data is still read from the legacy SQLite database through a `legacy` database alias.

## Structure Findings

| Area | Status | Evidence |
| --- | --- | --- |
| `manage.py` | Present | `django_backend/manage.py` |
| Settings | Present | `django_backend/config/settings/base.py`, `development.py`, `production.py`, `test.py` |
| URL routing | Present | `django_backend/config/urls.py`, `django_backend/apps/api/urls.py` |
| Django REST Framework | Present | `rest_framework` in `INSTALLED_APPS` |
| CORS | Present | `corsheaders` in `INSTALLED_APPS` and middleware |
| Apps | Present | `core`, `api`, `catalog`, `crm`, `sales`, `cms`, `accounts`, `common` |
| Views | Present | DRF function views under `django_backend/apps/api/views/` |
| Serializers | Present | Serializer helper modules under `django_backend/apps/api/serializers/` |
| Models | Present | 27 unmanaged legacy ORM models |
| Migrations | Not implemented for business apps | No app `migrations/` directories found under `django_backend/apps/` |

## Installed Apps

The Django settings include:

- Django built-in apps: `admin`, `auth`, `contenttypes`, `sessions`, `messages`, `staticfiles`
- Third-party apps: `corsheaders`, `rest_framework`
- Project apps: `apps.core`, `apps.common`, `apps.api`, `apps.catalog`, `apps.crm`, `apps.sales`, `apps.cms`, `apps.accounts`

## URL Routing

Root routing exists:

- `/`
- `/admin/`
- `/api/`
- `/api/v1/`

Business API routing exists under `/api/v1/` for:

- Catalog
- CRM
- Sales
- CMS
- Auth preparation
- Public replacement endpoints
- OpenAPI JSON
- AI chat

## Models

All inspected business models inherit from `LegacyReadOnlyModel` and use `managed = False`.

This means Django can query legacy tables, but Django does not own or migrate those tables.

Mapped model groups:

- Catalog: product, category, material, machine, process, capability tables
- CRM: customer, note, contact tables
- Sales: quote request, item, file tables
- CMS: page, menu, banner, newsletter tables
- Accounts: admin users, sessions, login attempts, password reset, 2FA, activity log tables

## Conclusion

Django structure is substantial and operational, but it is a parallel read-oriented migration layer, not a complete Django-owned application.

Status:

```text
DJANGO_PRESENT_BUT_NOT_FULL_OWNER
```
