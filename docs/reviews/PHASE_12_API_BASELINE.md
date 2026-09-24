# Phase 12 API Baseline

## Active APIs

### Legacy API

Legacy API namespace:

`/api/*`

Documented legacy endpoints include:

- `GET /api/home`
- `GET /api/products`
- `GET /api/products/{id}`
- `GET /api/product-categories`
- `GET /api/capabilities`
- `GET /api/news`
- `GET /api/openapi.json`
- `GET /api/health`
- `GET /api/version`
- `POST /api/contact`
- `POST /api/quote-request`
- `POST /api/ai/chat`

### Django Replacement API

Django namespace:

`/api/v1/*`

Current Django replacement endpoints include:

- `GET /api/v1/health/`
- `GET /api/v1/cutover/health/`
- `GET /api/v1/cutover/health/rollback/`
- `GET /api/v1/catalog/products/`
- `GET /api/v1/catalog/products/<id>/`
- `GET /api/v1/catalog/categories/`
- `GET /api/v1/catalog/materials/`
- `GET /api/v1/catalog/capabilities/`
- `GET /api/v1/crm/customers/`
- `GET /api/v1/crm/customers/<id>/`
- `GET /api/v1/crm/contact-requests/`
- `GET /api/v1/sales/quotes/`
- `GET /api/v1/sales/quotes/<id>/`
- `GET /api/v1/sales/quotes/<id>/files/`
- `GET /api/v1/cms/pages/`
- `GET /api/v1/cms/pages/<slug>/`
- `GET /api/v1/cms/menu/`
- `GET /api/v1/auth/profile/`
- `GET /api/v1/auth/permissions/`
- `GET /api/v1/public/home/`
- `GET /api/v1/news/`
- `GET /api/v1/openapi.json`
- `GET /api/v1/version/`
- `GET /api/v1/demo/aws/`
- `GET /api/v1/demo/external/weather/`
- `POST /api/v1/ai/chat/`

## Deprecated APIs

The legacy `/api/*` namespace is deprecated for future architecture, but it is
not shut down in production. Production remains `BLOCKED_SAFELY` until real
production traffic evidence and approvals are complete.

## Authentication

Legacy admin authentication exists in the custom backend. Django auth migration
currently exposes compatibility/read endpoints such as profile and permissions.

The Django replacement API still uses migration-safe controls and demo/internal
contracts. Full production authentication cutover is not complete.

## Authorization

Known authorization state:

- read APIs use read-only patterns
- write-intent replacements require guarded paths or admin token compatibility
- future write APIs require real auth, authorization and transaction review

## API Versions

| Version | Namespace | Status |
| --- | --- | --- |
| Legacy | `/api/*` | Active compatibility surface |
| v1 | `/api/v1/*` | Django replacement surface |

## Documentation Status

API documentation exists across:

- `backend/api/openapi.py`
- `django_backend/apps/api/views/replacement.py`
- `docs/api/`
- Phase 9, 10 and 11 review packages

## API Baseline Decision

Django `/api/v1/*` is the target replacement surface. Legacy `/api/*` remains
active until production evidence and approvals unlock a future production
shutdown.
