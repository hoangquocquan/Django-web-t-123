# Wave 6 Admin UI Audit

## Purpose

This audit records the legacy browser admin UI before Django UI cutover.

## Current Legacy Screens

| Screen | Legacy route | Legacy implementation |
| --- | --- | --- |
| Login/logout/account | `/admin/login`, `/admin/logout`, `/admin/account` | `backend/app.py` form rendering and session helpers |
| Dashboard | `/admin` | `backend/app.py` HTML dashboard |
| Products | `/admin/products*` | Legacy HTML forms, CMS service/repository calls |
| Customers | `/admin/customers*` | Legacy HTML forms, CMS service/repository calls |
| Inventory | Not a dedicated Django-owned UI before Wave 6 | Legacy CMS/admin patterns |
| Orders/quotes | `/admin/quotes*` | Legacy HTML quote workflow |
| Workflow/history | Mixed legacy admin pages and activity logs | Legacy services/repositories |

## Legacy Dependencies

- HTML is constructed inside `backend/app.py`.
- Form parsing is handled by the custom HTTP server.
- Permission checks call legacy auth/session helpers.
- CSS is shared with the public frontend and legacy admin shell.
- Legacy modules still cover CMS pages, media, banners, news, settings, AI, and developer tools.

## Migration Mapping

| Legacy UI responsibility | Django UI replacement |
| --- | --- |
| Browser login form | `/admin/login/` using `FoundationAuthService` |
| Dashboard counters | `/admin/` using Django ORM counters |
| Product create/update | `/admin/products/` and `/admin/products/<id>/` |
| Customer create/update | `/admin/customers/` and `/admin/customers/<id>/` |
| Inventory management | `/admin/inventory/` and stock adjustment forms |
| Order management | `/admin/orders/` and `/admin/orders/<id>/` |
| Workflow approval | `/admin/workflows/` |
| Transaction history | `/admin/transactions/` |

## Risk Assessment

| Risk | Mitigation |
| --- | --- |
| Operators need rollback | Legacy `backend/app.py` remains untouched |
| Built-in Django admin conflict | Technical Django admin moved to `/django-admin/` |
| Unauthorized admin writes | Every POST checks Foundation permissions |
| CSRF bypass | Django CSRF middleware and `{% csrf_token %}` are used |
| Partial admin migration | Remaining legacy screens are listed in final report |

## Decision

Proceed with Django browser admin UI for migrated domains only. Do not remove legacy admin yet.
