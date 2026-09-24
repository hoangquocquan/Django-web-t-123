# API Versioning Strategy

## Current Policy

New Django APIs use the `/api/v1/` prefix.

Examples:

```http
GET /api/v1/catalog/products/
GET /api/v1/crm/customers/
GET /api/v1/sales/quotes/
```

The legacy-compatible health endpoint remains available at `/api/health` to
protect old integrations.

## Backward Compatibility

Within `v1`:

- do not remove response fields without a minor phase and review approval
- add new optional fields only when tests and docs are updated
- keep error envelope stable
- keep pagination keys stable: `count`, `limit`, `offset`, `next_offset`, `results`

## Future Version Strategy

Create `/api/v2/` only when a breaking change is required, such as:

- database ownership migration changes response semantics
- write APIs introduce new workflow contracts
- authentication cutover changes permission behavior
- field names or nested structures must change

## Deprecation Rule

Before retiring a version:

1. document affected endpoints
2. provide replacement endpoint
3. run contract tests for both versions
4. create rollback plan
5. obtain architecture approval
