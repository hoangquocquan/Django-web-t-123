# Legacy Dependency Audit

## Phase

Phase 11 - Legacy System Shutdown

## Current Decision

```text
KEEP_LEGACY_ACTIVE
```

Phase 10.6 has not approved legacy shutdown. The current decision report says
production cutover is not verified, rollback completion is pending and business
approval is pending.

## Legacy Runtime Assets

| Asset | Location | Current status | Shutdown action |
|---|---|---|---|
| Legacy HTTP entrypoint | `backend/app.py` | Exists | Keep active |
| Legacy SQLite database | `backend/database/mecprecision.sqlite` | Exists | Keep as active rollback/archive source |
| Legacy schema | `backend/database/schema.sql` | Exists | Preserve |
| Legacy seed data | `backend/database/seed.sql` | Exists | Preserve |
| Legacy repositories/services | `backend/repositories`, `backend/services` | Exists | Preserve |
| Legacy uploads | `backend/uploads` | Exists | Preserve and include in archive plan |
| Legacy logs | `backend/logs` | Exists | Preserve for audit trail |

## Django Dependencies Still Referencing Legacy

The migrated Django modules still contain read-only legacy ORM mappings and
repositories that use the `legacy` database alias.

| Django area | Dependency type | Reason |
|---|---|---|
| `django_backend/apps/catalog` | unmanaged read-only ORM | Catalog still maps legacy tables |
| `django_backend/apps/crm` | unmanaged read-only ORM | CRM data still maps legacy tables |
| `django_backend/apps/sales` | unmanaged read-only ORM | Quote data still maps legacy tables |
| `django_backend/apps/cms` | unmanaged read-only ORM | CMS pages, menus and banners still map legacy tables |
| `django_backend/apps/accounts` | compatibility services/repositories | Auth compatibility still reads legacy admin data |
| `django_backend/conftest.py` | test fixture | Tests copy SQLite into read-only fixture |
| `scripts/phase10_*` | cutover/readiness tooling | Validation scripts compare or protect legacy source |

## Remaining Shutdown Blockers

| Blocker | Current status |
|---|---|
| Production cutover approved | Pending |
| Zero production traffic to legacy APIs | Not confirmed |
| Rollback window closed | Pending |
| Archive restore verified | Pending |
| Business owner approval | Pending |
| Architecture approval marker `ALLOW_PHASE_11` | Missing |

## Risk Analysis

Shutting down legacy now would be unsafe because Django still has explicit
legacy database dependencies and the production cutover report is still marked
`NOT EXECUTED`.

## Decision

Do not shut down, delete or archive-away the legacy runtime in this phase. Keep
Phase 11 as a readiness and governance package until the blocker list is
cleared.
