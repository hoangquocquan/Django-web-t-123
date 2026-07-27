# Phase 12 Codebase Audit Report

## Backend Structure

The legacy backend is organized as a custom Python HTTP application:

| Directory | Purpose |
| --- | --- |
| `backend/app.py` | Main custom HTTP server and routing surface |
| `backend/controllers/` | Request/page handling helpers |
| `backend/services/` | Business logic and orchestration |
| `backend/repositories/` | SQLite data access |
| `backend/auth/` | Password/session helpers |
| `backend/middleware/` | Request safety and error handling helpers |
| `backend/database/` | SQLite schema, seed and connection utilities |
| `backend/api/` | Legacy OpenAPI support |

The Django backend is organized by domain:

| App | Purpose |
| --- | --- |
| `core` | Health and cutover status |
| `api` | Versioned API facade under `/api/v1/*` |
| `catalog` | Product/category/material/capability ORM access |
| `crm` | Customer/contact data access |
| `sales` | Quotation data access |
| `cms` | Pages/menu/banner/newsletter data access |
| `accounts` | Admin user/auth compatibility read model |
| `common` | Shared model/repository utilities |

## Frontend Structure

The frontend is a static multi-page site:

- root pages are stored directly under `frontend/`
- `frontend/css/styles.css` contains shared styles
- `frontend/js/app.js` contains browser behavior
- assets live in `frontend/images/`, `frontend/icons/` and `frontend/fonts/`

## Dependencies

Legacy backend requirements:

- `pypdf>=4.3.1`
- `Django>=5.0,<6.0`

Django backend requirements:

- `django`
- `djangorestframework`
- `django-cors-headers`
- `python-dotenv`
- `pytest`
- `pytest-django`
- `psycopg[binary]`

Infrastructure dependencies:

- Docker
- Docker Compose
- Redis container
- Nginx container

## Unused Or Transitional Modules

| Area | Observation | Recommendation |
| --- | --- | --- |
| `backend/app.py` | Large custom server still owns many routes | Keep until production decommission is approved |
| Legacy backup scripts | Earlier simple backup scripts remain | Keep for reference, prefer Phase 11.2 archive workflow for audit |
| Django default DB | `db.sqlite3` fallback exists for Django default DB | Keep for development, document production database target separately |
| Static frontend | Not yet fully separated from legacy backend assumptions | Audit API calls before frontend modernization |

## Technical Debt

- Legacy backend routing remains centralized in a large `backend/app.py` file.
- Some older comments/docs show mojibake encoding, especially Vietnamese text
  created before encoding cleanup.
- CI currently focuses on legacy compile/unit checks and Docker build; it does
  not yet run the full migration test script.
- Dockerfile still starts the legacy backend, not Django.
- Business write behavior in Django is still migration-safe/readiness oriented,
  not full production write ownership.

## Code Quality Issues

| Issue | Risk | Recommendation |
| --- | --- | --- |
| Large legacy app file | Harder debugging and review | Avoid new features there; continue Django migration |
| Dual backend surfaces | Operational confusion | Keep API baseline and route ownership matrix updated |
| Demo admin token in tests/API compatibility | Security risk if exposed | Replace with real auth before public production exposure |
| Static frontend/API coupling | Future integration risk | Create frontend API contract tests before UI cutover |

## Audit Result

The codebase is migration-ready for the next planning phase, but not yet ready
for broad production hardening without a dedicated security and deployment
review.
