# Django Backend - Migration Step 1

This folder is a new Django backend that runs in parallel with the legacy Python HTTP server.

No legacy business logic has been moved in this step.
No legacy files are changed.
No database migration is performed.

## Setup environment

```powershell
cd django_backend
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
```

Update `.env` when needed:

```env
SECRET_KEY=
DEBUG=True
DATABASE_URL=
REDIS_URL=
ALLOWED_HOSTS=localhost,127.0.0.1
```

If `DATABASE_URL` is empty, Django falls back to:

```text
django_backend/db.sqlite3
```

## Run Django

```powershell
cd django_backend
python manage.py check
python manage.py runserver
```

Legacy backend remains unchanged and still runs separately:

```powershell
python backend\app.py
```

## Health check APIs

Root:

```http
GET /
```

Expected response:

```json
{
  "status": "django running",
  "version": "step-1"
}
```

Migration health check:

```http
GET /api/health/
```

Expected response:

```json
{
  "success": true,
  "message": "Django migration step 1 completed"
}
```

## Migration roadmap

1. Step 1: Initialize Django backend parallel to the legacy system.
2. Step 2: Analyze existing database schema and convert legacy models to Django ORM models.
3. Step 3: Add read-only APIs matching legacy data.
4. Step 4: Move selected business services gradually.
5. Step 5: Add authentication, permissions, tests, and deployment pipeline.

The priority is safety and backward compatibility.
