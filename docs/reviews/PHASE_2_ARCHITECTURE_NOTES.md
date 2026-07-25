# Phase 2 Architecture Notes

## 1. Objective

Phase 2 creates the Django foundation for the migration project.

This phase is infrastructure-only.

No business logic was migrated.
No Django ORM models were created.
No database migrations were created or executed.
No legacy backend code was modified.

## 2. Django Structure

Main folder:

```text
django_backend/
```

Important structure:

```text
django_backend/
  manage.py
  config/
    settings/
      base.py
      development.py
      test.py
      production.py
    urls.py
    asgi.py
    wsgi.py
  apps/
    core/
    common/
  tests/
  logs/
  requirements.txt
  pytest.ini
  .env.example
  README.md
```

## 3. Settings Strategy

Settings are split by environment:

| File | Purpose |
|---|---|
| `base.py` | Shared infrastructure settings |
| `development.py` | Local development defaults |
| `test.py` | Test database and test performance settings |
| `production.py` | Production security defaults |

Default runtime setting:

```text
config.settings.development
```

The settings package is designed so future phases can add production deployment config without mixing it into local development settings.

## 4. App Strategy

### Core App

`apps.core` is intentionally small.

Allowed Phase 2 responsibilities:

- health check
- infrastructure exceptions later
- middleware helpers later
- constants later
- logging/error conventions later

Current endpoint:

```text
GET /api/v1/health/
```

Response:

```json
{
  "success": true,
  "message": "Django foundation ready",
  "phase": 2
}
```

### Common App

`apps.common` is a skeleton only.

Prepared folders:

```text
utils/
exceptions/
constants/
helpers/
```

Important boundary:

`common` must not become a giant app. It should not contain CMS, media, catalog, CRM, sales, or AI business logic.

## 5. Environment Strategy

Environment variables are loaded with:

```text
python-dotenv
```

Safe template:

```text
django_backend/.env.example
```

Real `.env` files must not be committed.

Supported variables:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DATABASE_URL`
- `REDIS_URL`
- `EMAIL_CONFIG`
- `TIME_ZONE`
- `CORS_ALLOWED_ORIGINS`
- `DJANGO_LOG_LEVEL`
- `APP_LOG_LEVEL`

## 6. Logging Strategy

Logging supports:

- console logging
- rotating file logging

Log folder:

```text
django_backend/logs/
```

Log files are ignored by Git.

Security note:

Application code must not log secrets, passwords, tokens, or raw environment values.

## 7. Database Strategy

Phase 2 configures database connection only.

Fallback:

```text
SQLite development database at django_backend/db.sqlite3
```

Future support:

```text
PostgreSQL via DATABASE_URL
```

Strict Phase 2 limits:

- no legacy database migration
- no Django business models
- no migrations generated
- no `migrate` command required for legacy data

## 8. API Strategy

DRF is configured for JSON APIs.

Versioned API prefix:

```text
/api/v1/
```

Phase 2 exposes only infrastructure health checks.

No business endpoints are added.

## 9. Testing Strategy

Test framework:

```text
pytest
pytest-django
```

Test config:

```text
django_backend/pytest.ini
```

Initial test:

```text
tests/test_health.py
```

Expected validation:

```text
python manage.py check
pytest
```

## 10. Security Review

Production security settings are prepared in:

```text
config/settings/production.py
```

Includes:

- `DEBUG=False`
- SSL redirect option
- secure cookies
- HSTS
- content type nosniff
- denied frame options

No authentication migration is performed in Phase 2.

## 11. Next Step

After architecture review approval:

```text
Phase 3 - Database Mapping / Legacy Schema Analysis
```

Do not create Django ORM models until database mapping is reviewed.
