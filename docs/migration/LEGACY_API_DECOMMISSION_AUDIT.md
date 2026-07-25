# Legacy API Decommission Audit

## Phase

Phase 11.1 - Legacy API Decommission

## Current Decision

```text
KEEP_LEGACY_API_ACTIVE
```

Legacy API routes must not be disabled yet because production traffic evidence
and full Django replacement coverage are not available in this environment.

## Legacy API Sources

| Source | Purpose |
|---|---|
| `backend/app.py` | Legacy HTTP route dispatch and API handling |
| `backend/api/openapi.py` | Legacy OpenAPI schema |
| `backend/controllers/api_controller.py` | Legacy API controller functions |
| `backend/tests/test_app_behavior.py` | Legacy API behavior tests |

## Django API Sources

| Source | Purpose |
|---|---|
| `django_backend/apps/core/urls.py` | Health and cutover status endpoints |
| `django_backend/apps/api/urls.py` | Migrated read-only business APIs |
| `django_backend/apps/api/tests/` | API contract and hardening tests |

## Decommission Blockers

| Blocker | Current status |
|---|---|
| Django API contracts pass in production | Not verified |
| Traffic logs prove zero legacy API clients | Not provided |
| Client contract tests pass | Pending |
| Rollback window respected | Pending |
| Access logs archived | Pending |
| Write endpoints migrated to Django | Not complete |
| AI/demo/API docs endpoints migrated | Not complete |

## Decision

Do not disable, redirect or remove legacy API routes in this phase. Keep this
phase as a readiness package until all blockers are cleared.
