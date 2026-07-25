# Legacy API Compatibility Matrix

## Purpose

Map legacy API routes to Django replacements before decommission.

| Method | Legacy route | Django replacement | Ready | Notes |
|---|---|---|---|---|
| GET | `/api/health` | `/api/v1/health/` | Yes | Contract tested |
| GET | `/api/products` | `/api/v1/catalog/products/` | Yes | Read-only replacement exists |
| GET | `/api/products/{id}` | `/api/v1/catalog/products/{id}/` | Yes | Read-only replacement exists |
| GET | `/api/product-categories` | `/api/v1/catalog/categories/` | Yes | Read-only replacement exists |
| GET | `/api/news` | TBD | No | Django news API missing |
| GET | `/api/home` | TBD | No | Home aggregate API missing |
| GET | `/api/capabilities` | TBD | No | Capabilities API missing |
| GET | `/api/openapi.json` | TBD | No | Django OpenAPI endpoint missing |
| GET | `/api/version` | TBD | No | Django version endpoint missing |
| GET | `/api/aws-demo` | TBD | No | Demo endpoint not migrated |
| GET | `/api/external/weather` | TBD | No | External weather demo not migrated |
| POST | `/api/contact` | `/api/v1/crm/contact-requests/` | No | Django endpoint is read-only |
| POST | `/api/quote-request` | `/api/v1/sales/quotes/` | No | Django endpoint is read-only |
| POST | `/api/ai/chat` | TBD | No | AI API not migrated |
| POST/PUT/DELETE | `/api/products` | TBD | No | Django write API not available |

## Summary

```text
Ready replacements: 4
Not ready replacements: 11
```

Legacy API decommission is not approved until every production-used endpoint has
a verified Django replacement or an approved removal decision.
