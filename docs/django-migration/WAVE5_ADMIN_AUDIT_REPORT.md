# Wave 5 Admin Audit Report

## Purpose

This report records the legacy admin surface before the Wave 5 Django admin migration.

## Legacy Admin Surface

The legacy admin interface is still implemented in `backend/app.py` as server-rendered HTML pages and form handlers.

Key legacy areas found:

| Area | Legacy route pattern | Current owner before Wave 5 |
| --- | --- | --- |
| Login and account | `/admin/login`, `/admin/logout`, `/admin/account` | Legacy custom HTTP server |
| Dashboard | `/admin` | Legacy custom HTTP server |
| Products | `/admin/products*` | Legacy custom HTTP server, CMS repositories |
| Categories | `/admin/categories*` | Legacy custom HTTP server, CMS repositories |
| News | `/admin/news*` | Legacy custom HTTP server, CMS repositories |
| Media | `/admin/media*` | Legacy custom HTTP server, filesystem upload helpers |
| Pages and menu | `/admin/pages*`, `/admin/menus*` | Legacy custom HTTP server, CMS repositories |
| Contacts and quotes | `/admin/contacts*`, `/admin/quotes*` | Legacy custom HTTP server, CRM/Sales repositories |
| Users and settings | `/admin/users*`, `/admin/settings*` | Legacy custom HTTP server, auth/user repositories |
| AI and Developer | `/admin/ai*`, `/admin/developer*` | Legacy custom HTTP server, AI/developer services |

## Legacy Dependencies

- `backend/app.py` renders admin HTML, parses forms, redirects, and calls service functions directly.
- `backend/services/auth_service.py`, `backend/services/users_service.py`, and `backend/auth/*` own legacy admin authentication/session behavior.
- `backend/services/cms_service.py`, `backend/repositories/cms_repository.py`, and related repositories still support broad CMS admin modules.
- `backend/services/activity_service.py` records legacy admin activity logs.

## Migration Risk

| Risk | Impact | Wave 5 response |
| --- | --- | --- |
| Duplicate admin entry points | Operators may use either legacy or Django admin APIs | Preserve both during migration and document ownership |
| Permission mismatch | A role could gain/lose access during cutover | Reuse `FoundationPermissionService` for Django admin APIs |
| Accidental legacy shutdown | Existing web admin could break | No legacy files were deleted or disabled |
| Partial CMS coverage | Some admin modules are not Django-owned yet | Mark as remaining migration work |

## Audit Decision

Wave 5 can safely create Django-owned admin APIs for migrated domains while keeping legacy admin pages available for compatibility.
