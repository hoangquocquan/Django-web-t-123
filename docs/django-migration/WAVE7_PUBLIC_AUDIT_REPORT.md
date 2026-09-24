# Wave 7 Public Website Audit Report

## Purpose

This audit records the public website before Django ownership migration.

## Current Public Pages

| Page | Legacy URL | Legacy owner |
| --- | --- | --- |
| Homepage | `/` | Legacy `backend/app.py` and frontend assets |
| Products | `/products` | Legacy public rendering and product data |
| Product detail | `/product/<slug>` or legacy equivalent | Legacy catalog rendering |
| Technology | `/technology` | Legacy static/dynamic content |
| News | `/news` | Legacy CMS rendering |
| Contact | `/contact` | Legacy form handling |

## Legacy Dependencies

- Public HTML is rendered by legacy code and static frontend assets.
- Product content historically comes from catalog tables and admin CMS workflows.
- Contact/quote submissions are handled by legacy routes or API replacement contracts.
- Public SEO metadata was manually embedded in legacy templates.

## Django Replacement Mapping

| Legacy responsibility | Django replacement |
| --- | --- |
| `/` | `apps.website.views.home` |
| `/products` | `apps.website.views.products` |
| `/product/<slug>` | `apps.website.views.product_detail` |
| `/technology` | `apps.website.views.technology` |
| `/news` | `apps.website.views.news` |
| `/news/<slug>` | `apps.website.views.news_detail` |
| `/contact` | `apps.website.views.contact` |

## Migration Risks

| Risk | Mitigation |
| --- | --- |
| SEO URL breakage | Keep URL paths compatible and support slash/no-slash variants |
| Missing public content | Use Django-owned products and safe fallback capability content |
| Form abuse | Use Django forms, CSRF, captcha validation, and no secret exposure |
| Rollback need | Legacy public files remain untouched |

## Decision

Proceed with Django rendering for public pages while preserving legacy files for rollback.
