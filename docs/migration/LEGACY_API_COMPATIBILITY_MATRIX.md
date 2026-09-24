# Legacy API Compatibility Matrix

## Purpose

Map legacy API routes to Django replacements before decommission.

| Method | Legacy route | Django replacement | Status | Notes |
|---|---|---|---|---|
| GET | `/api/health` | `/api/v1/health/` | READY | Contract tested |
| GET | `/api/products` | `/api/v1/catalog/products/` | READY | Read replacement exists |
| GET | `/api/products/{id}` | `/api/v1/catalog/products/{id}/` | READY | Detail replacement exists |
| GET | `/api/product-categories` | `/api/v1/catalog/categories/` | READY | Category replacement exists |
| GET | `/api/news` | `/api/v1/news/` | READY | CMS-backed news replacement |
| GET | `/api/home` | `/api/v1/public/home/` | READY | Django aggregate replacement |
| GET | `/api/capabilities` | `/api/v1/catalog/capabilities/` | READY | Capability replacement exists |
| GET | `/api/openapi.json` | `/api/v1/openapi.json` | READY | Compact Django OpenAPI replacement |
| GET | `/api/version` | `/api/v1/version/` | READY | Version replacement exists |
| GET | `/api/aws-demo` | `/api/v1/demo/aws/` | READY | Local deterministic demo replacement |
| GET | `/api/external/weather` | `/api/v1/demo/external/weather/` | READY | Network-free weather demo replacement |
| POST | `/api/contact` | `/api/v1/crm/contact-requests/` | READY | Validated Django write intent |
| POST | `/api/quote-request` | `/api/v1/sales/quotes/` | READY | Validated Django write intent |
| POST | `/api/ai/chat` | `/api/v1/ai/chat/` | READY | Migration-safe AI response |
| POST/PUT/DELETE | `/api/products` | `/api/v1/catalog/products/` and `/api/v1/catalog/products/{id}/` | READY | Admin-token protected write intent |

## Summary

```text
Ready replacements: 15
Not ready replacements: 0
```

Legacy API decommission is still not approved until production traffic logs,
client contract tests, rollback window and architecture approval are verified.
