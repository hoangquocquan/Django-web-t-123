# Phase 12 System Architecture Baseline

## Current Architecture

The project currently contains three major application surfaces:

| Layer | Current state |
| --- | --- |
| Frontend | Static HTML/CSS/JavaScript in `frontend/` |
| Legacy backend | Custom Python HTTP server in `backend/app.py` |
| Django backend | Django + Django REST Framework in `django_backend/` |
| Database | Legacy SQLite database at `backend/database/mecprecision.sqlite` |
| Infrastructure | Docker, Docker Compose, Nginx sample config and GitHub Actions CI |

## Frontend

The frontend is page-based and contains:

- `frontend/index.html`
- `frontend/san-pham.html`
- `frontend/cong-nghe.html`
- `frontend/tin-tuc.html`
- `frontend/lien-he.html`
- shared JavaScript in `frontend/js/app.js`
- shared styling in `frontend/css/styles.css`

The frontend still has static files and legacy integration assumptions. Future
phases should decide whether it remains static, becomes Django-rendered, or is
replaced by a separate frontend app.

## Backend

The legacy backend remains present and includes:

- controllers
- services
- repositories
- auth
- middleware
- cache
- validators
- database utilities

The Django backend is structured by app:

- `accounts`
- `api`
- `catalog`
- `cms`
- `common`
- `core`
- `crm`
- `sales`

The Django backend currently provides replacement read/API surfaces while using
legacy database access patterns designed for migration safety.

## Database

The active legacy database is SQLite:

`backend/database/mecprecision.sqlite`

The Django `legacy` database connection points to the same SQLite file in
read-only URI mode. Database archive Phase 11.2 is complete and verified.

## API Structure

Current API split:

- legacy API namespace: `/api/*`
- Django replacement namespace: `/api/v1/*`
- health endpoints exist under both `/api/` and `/api/v1/`

Legacy `/api/*` remains a compatibility/rollback surface until real production
evidence and approvals exist.

## External Integrations

Known or prepared integrations:

- Open-Meteo demo via legacy backend external weather endpoint
- Redis prepared in Docker Compose
- Nginx reverse proxy sample
- GitHub Actions CI
- Ollama/AI related local features from earlier development

No production external integration was changed in this phase.

## Deployment Model

Current deployment assets:

- `Dockerfile` runs `python backend/app.py`
- `docker-compose.yml` runs legacy web, Redis and Nginx
- `nginx/nginx.conf` proxies traffic to the web service
- `.github/workflows/ci.yml` runs syntax checks, unit tests and Docker build

The Docker entrypoint still targets the legacy backend. Django production
deployment remains a future cutover topic.

## Before And After Migration Comparison

| Area | Before migration | Current baseline |
| --- | --- | --- |
| Runtime | Custom Python backend only | Legacy backend plus Django backend |
| API | `/api/*` legacy routes | `/api/*` legacy plus `/api/v1/*` replacement |
| Database ownership | Legacy SQLite | Legacy SQLite archived and read via Django unmanaged/read-only patterns |
| Governance | Informal local workflow | Phase-based Git workflow, review packages and audit documents |
| Testing | Legacy tests plus manual checks | Legacy, Django, migration, evidence and archive tests |
| Production shutdown | Not prepared | Training shutdown complete, production still blocked safely |

## Baseline Decision

Phase 12 is documentation-only. No production behavior, route, database schema
or deployment configuration was changed.
