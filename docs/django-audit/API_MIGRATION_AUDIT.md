# API Migration Audit

## Scope

This audit inspected Django API routing, views, serializers, permissions, and legacy API replacement behavior without changing code.

## Django API Status

Django exposes API routes under:

```text
/api/
/api/v1/
```

`django_backend/apps/api/urls.py` defines 23 route declarations.

## API Areas

| Area | Django API Present | Notes |
| --- | --- | --- |
| Catalog | Yes | Product/category/material/capability endpoints |
| CRM | Yes | Customer and contact request endpoints |
| Sales | Yes | Quote endpoints |
| CMS | Yes | Page and menu endpoints |
| Auth | Yes | Profile and permission preparation endpoints |
| Public replacement | Yes | Home, news, OpenAPI, version, demo, AI chat |

## Django REST Framework Usage

The API layer uses:

- `@api_view`
- DRF `Response`
- DRF permissions
- serializer helper modules

Serializer modules exist for:

- auth
- catalog
- cms
- crm
- sales

## Authentication And Permissions

The API layer uses a mixed state:

- Some read-only endpoints use `ReadOnlyApiPermission`.
- Some replacement/write-intent endpoints use `AllowAny`.
- Full Django authentication ownership is not established.
- Legacy admin/session/auth tables remain mapped read-only.

## Write Behavior

Some Django endpoints accept POST/PUT/DELETE-shaped replacement contracts:

- `POST /api/v1/catalog/products/`
- `PUT /api/v1/catalog/products/<id>/`
- `DELETE /api/v1/catalog/products/<id>/`
- `POST /api/v1/crm/contact-requests/`
- `POST /api/v1/sales/quotes/`

However, inspected replacement submission code stores write intent in memory and deliberately does not write to legacy SQLite.

This is not full business write migration.

## Legacy API Status

Legacy backend API code still exists:

- `backend/controllers/api_controller.py`
- `backend/api/openapi.py`
- `backend/app.py`

Documentation from earlier phases describes API cutover as read-only/compatibility-first, with rollback to legacy preserved.

## Conclusion

APIs are partially migrated to Django and DRF. Read-only and compatibility endpoints exist, but database-backed writes and full auth/permission ownership are not complete.

Status:

```text
API_PARTIALLY_MIGRATED
```
