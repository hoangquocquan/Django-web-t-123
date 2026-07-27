# Docker Architecture

## Container Strategy

Phase 13.1 creates a local Docker build foundation for the Django migration
backend. The goal is reproducible image creation and validation, not production
deployment.

The image is built locally and tagged as:

```text
mecprecision-vietnam:phase-13.1
```

No image is pushed to an external registry in this phase.

## Application Container

The application container:

- uses `python:3.12-slim`
- installs Django and legacy requirements
- runs as non-root user `appuser`
- exposes port `8000`
- starts Django with `python django_backend/manage.py runserver 0.0.0.0:8000`
- includes a local HTTP health check against `/api/v1/health/`

## Database Container

`docker-compose.yml` defines a PostgreSQL service for future CI/staging use.

The current Django image still uses local SQLite defaults unless `DATABASE_URL`
is changed. The legacy SQLite database remains read-only through
`LEGACY_DATABASE_URL`.

## Network Model

Compose creates one isolated bridge network:

```text
mecprecision-local
```

Services on this network:

- `web`
- `database`
- `redis`

Only the web service exposes port `8000` to the host.

## Volume Strategy

Named volumes:

- `media-data` for uploaded media
- `postgres-data` for PostgreSQL state
- `redis-data` for Redis state

Runtime data is separated from the image so rebuilds remain reproducible.

## Environment Handling

The image defines safe local defaults only. Real secrets must come from an
environment manager or CI secret store in later phases.

Rules:

- Do not commit real secrets.
- Do not push local image externally in Phase 13.1.
- Do not deploy production from this compose file.
- Override environment values through CI or `.env` only in controlled contexts.
