# Django Backend - Phase 2 Foundation

This folder contains the parallel Django backend for the `mecprecision-vietnam` migration.

Phase 2 creates infrastructure only:

- split settings
- environment loading
- logging foundation
- Django REST Framework setup
- core health API
- common app skeleton
- pytest foundation

Phase 2 does not create business models, database migrations, authentication migration, or legacy business logic.

## Setup

```powershell
cd django_backend
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
```

## Settings

Default local settings:

```text
config.settings.development
```

Available settings:

| File | Purpose |
|---|---|
| `config/settings/base.py` | Shared apps, middleware, database, static/media, logging, DRF |
| `config/settings/development.py` | Local development defaults |
| `config/settings/test.py` | Test database and faster test settings |
| `config/settings/production.py` | Production security defaults |

## Environment

Real `.env` files must not be committed.

Safe template:

```text
.env.example
```

Important variables:

```env
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=
REDIS_URL=
EMAIL_CONFIG=
```

If `DATABASE_URL` is empty, Django uses local SQLite:

```text
django_backend/db.sqlite3
```

PostgreSQL URLs are prepared for future phases, but Phase 2 does not migrate any data.

## Health APIs

Versioned API:

```http
GET /api/v1/health/
```

Compatibility health API:

```http
GET /api/health/
```

Expected response:

```json
{
  "success": true,
  "message": "Django foundation ready",
  "phase": 2
}
```

## Run Checks

```powershell
cd django_backend
python manage.py check
pytest
```

## Run Server

```powershell
cd django_backend
python manage.py runserver
```

Legacy backend remains separate:

```powershell
python backend\app.py
```

## Migration Boundary

Do not add legacy business models in Phase 2.

The next approved phase should review database mapping before any Django ORM model is created.
