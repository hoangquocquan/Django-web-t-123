# Phase 12 Security Baseline

## Authentication

Legacy admin authentication exists in the custom backend and includes:

- login/logout
- password reset flow
- password hashing compatibility
- sessions
- CSRF helpers
- account lock/unlock
- 2FA-related tables

Django auth endpoints currently provide compatibility/read surfaces, not final
production login cutover.

## Secrets Management

Current Django settings load environment variables with `python-dotenv`.

Known baseline:

- `.env` and `.env.*` are ignored
- `.env.example` files are allowed
- production settings disable debug and enable secure cookies/HSTS defaults
- legacy settings still include demo/default values for local development

Risk:

- demo tokens and local defaults must not be used for public production.

## Permissions

Current API security review states:

- read-only API permissions exist for migrated business APIs
- sensitive auth fields are not exposed in profile responses
- write APIs require additional transaction and authorization review

## Dependencies

Python dependencies:

- Django
- Django REST Framework
- django-cors-headers
- python-dotenv
- pytest / pytest-django
- psycopg
- pypdf

Security recommendation:

- add dependency vulnerability scanning before production deployment
- pin versions in production lock files
- review transitive dependencies

## Known Risks

| Risk | Status | Recommendation |
| --- | --- | --- |
| Legacy `/api/*` still active | Open | Keep evidence gate and production approval requirement |
| Production evidence incomplete | Open | Collect real IIS/API evidence before shutdown |
| Demo admin token compatibility | Open | Replace with real auth before public exposure |
| Business data exposed by read APIs | Open | Add production authentication and authorization policy |
| Secrets/logging | Controlled but needs hardening | Add redaction tests and secret scanning |
| SQLite archive sensitivity | Controlled | Keep `.sqlite` backups out of Git and encrypt production archives |

## Security Baseline Decision

The system is ready for a dedicated security hardening phase. It is not yet
ready for public production exposure of all business APIs without auth,
authorization and secret-management review.
