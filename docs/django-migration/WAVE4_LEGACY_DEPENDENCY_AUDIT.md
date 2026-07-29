# Wave 4 Legacy Dependency Audit

## Summary

Wave 4 is an assessment and reduction wave. It does not delete legacy code or shut down production services.

Django now owns the primary foundation, business core, and transaction domains. The legacy system still provides compatibility routes, CMS/admin surfaces, public page rendering, media/upload utilities, AI/admin helper features, settings, and selected infrastructure services.

## Dependency Matrix

| Component | Current Owner | Django Replacement | Migration Status | Risk Level |
|---|---|---|---|---|
| Authentication, users, roles | Django-owned foundation tables | `apps.foundation` | Migrated in Wave 1 | Medium |
| Newsletter | Django-owned newsletter table | `apps.newsletter` | Migrated before Wave 1 | Low |
| Product write ownership | Django-owned business product table | `apps.business_core.BusinessProduct` | Migrated in Wave 2 | Medium |
| Customer write ownership | Django-owned business customer table | `apps.business_core.BusinessCustomer` | Migrated in Wave 2 | Medium |
| Inventory ownership | Django-owned inventory tables | `InventoryWarehouse`, `InventoryItem`, `InventoryTransaction` | Migrated in Wave 2 | Medium |
| Order/workflow/history | Django-owned transaction tables | `apps.transaction_domain` | Migrated in Wave 3 | Medium |
| Legacy catalog read APIs | Legacy unmanaged models | `/api/v1/catalog/...` plus business APIs | Shared compatibility | Medium |
| Legacy quote read APIs | Legacy unmanaged sales models | `/api/v1/orders/`, `/api/v1/transactions/` | Shared compatibility | High |
| CMS pages, menus, banners | Legacy unmanaged CMS models and legacy admin | `apps.cms` read-only only | Shared, read-only in Django | Medium |
| News content | Legacy tables and CMS/public APIs | Partial Django replacement via CMS-backed API | Shared | Medium |
| Contact requests | Legacy CRM/contact tables | CRM read-only plus transaction/business ownership | Shared | Medium |
| AI operations | Legacy `backend/services/ai_service.py` | AI review/factory tooling; runtime AI still legacy | Shared | Medium |
| Media/uploads | Legacy filesystem upload folders | No full Django media manager ownership yet | Legacy-only operationally | High |
| Settings/system config | Legacy `system_settings` and services | Django settings for backend runtime only | Shared | Medium |
| Queue/events/notifications | Legacy `job_queue`, `enterprise_events`, `notifications` | Transaction history owns event audit only | Shared | Medium |
| Payment processing | No approved Django owner | None | Legacy/future project | High |
| Custom HTTP server/pages | `backend/app.py` | Django API backend only | Legacy infrastructure remains | High |

## Remaining Legacy Folders

- `backend/app.py`
- `backend/controllers/`
- `backend/repositories/`
- `backend/services/`
- `backend/auth/`
- `backend/database/`
- `backend/uploads/`
- `backend/cache/`
- `backend/middleware/`

## Final Assessment

Legacy should remain available until route-level traffic evidence proves Django API parity, CMS/admin ownership is explicitly migrated, media handling is replaced, and payment is approved as a separate project.
