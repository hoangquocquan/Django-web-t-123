# Legacy API Replacement Status

## Phase

Phase 11.1.1 - Django API Replacement Completion

## Coverage

```text
15/15 legacy API route groups documented
15/15 legacy API route groups have Django replacements
```

## Status Table

| Priority | Legacy route group | Django replacement | Compatibility status |
|---|---|---|---|
| High | `POST /api/contact` | `POST /api/v1/crm/contact-requests/` | READY |
| High | `POST /api/quote-request` | `POST /api/v1/sales/quotes/` | READY |
| High | Product write operations | `/api/v1/catalog/products/` | READY |
| Medium | `POST /api/ai/chat` | `POST /api/v1/ai/chat/` | READY |
| Medium | `GET /api/openapi.json` | `GET /api/v1/openapi.json` | READY |
| Medium | `GET /api/version` | `GET /api/v1/version/` | READY |
| Medium | `GET /api/aws-demo` | `GET /api/v1/demo/aws/` | READY |
| Medium | `GET /api/external/weather` | `GET /api/v1/demo/external/weather/` | READY |
| Low | `GET /api/home` | `GET /api/v1/public/home/` | READY |
| Low | `GET /api/news` | `GET /api/v1/news/` | READY |
| Low | `GET /api/capabilities` | `GET /api/v1/catalog/capabilities/` | READY |
| Existing | `GET /api/health` | `GET /api/v1/health/` | READY |
| Existing | Catalog read routes | `/api/v1/catalog/...` | READY |
| Existing | CRM read routes | `/api/v1/crm/...` | READY |
| Existing | Sales/CMS/Auth read routes | `/api/v1/...` | READY |

## Write Replacement Note

Write replacements validate request data and create Django API write-intent
responses without writing to the legacy SQLite database. This protects migration
safety while completing client-facing replacement contracts.

## Remaining Decommission Blockers

- Production traffic logs must prove no clients still call legacy `/api/...`.
- Client contract tests must pass against production Django routes.
- Rollback window must be respected.
- Architecture reviewer must approve decommission.
