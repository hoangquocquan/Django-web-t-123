# API Health Cutover Contract

## Selected Endpoint

Phase 9 cuts over only the low-risk health check endpoint.

Legacy endpoint:

```http
GET /api/health
```

Django endpoints:

```http
GET /api/health
GET /api/health/
GET /api/v1/health
GET /api/v1/health/
```

## Preserved Response Shape

The Django compatibility adapter preserves the public keys from the legacy
`get_health_status()` response:

| Key | Meaning |
|---|---|
| `status` | Overall service state: `ok` or `degraded` |
| `api_version` | Legacy API version value |
| `environment` | Runtime environment |
| `database` | Legacy SQLite availability |
| `sqlite_version` | SQLite runtime version |
| `redis_enabled` | Whether legacy Redis cache is enabled |

## Cutover Boundary

This phase does not cut over write APIs, authentication, CMS CRUD, catalog CRUD,
CRM workflows, or quotation workflows.

## Compatibility Rule

Old clients must be able to call `/api/health` and continue reading the same
top-level keys. Any future additions must be documented and covered by contract
tests before approval.
