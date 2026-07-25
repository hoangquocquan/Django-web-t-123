# API Cutover Strategy

## Phase 9 Goal

Move one low-risk legacy API route to Django while preserving compatibility and
keeping rollback simple.

## Selected Route

`GET /api/health`

Reasons:

- read-only
- no authentication required
- no business transaction
- no database mutation
- simple response contract

## Adapter Pattern

The Django core app owns an API compatibility adapter:

```text
request
  -> Django URL route
  -> core view
  -> compatibility adapter
  -> legacy-compatible JSON response
```

## Route Strategy

Both unversioned and versioned routes are supported:

```http
GET /api/health
GET /api/v1/health
```

The unversioned route protects old clients. The versioned route becomes the
standard for new integrations.

## Validation Strategy

Automated tests must verify:

- legacy-compatible response keys
- endpoint accepts trailing and non-trailing slash
- cutover metadata is available
- rollback smoke endpoint is available
- write methods are rejected

## Future Cutover Rule

Future API routes should only be moved after:

- ORM/service parity is approved
- contract tests exist
- rollback plan is documented
- write APIs have transaction tests
- auth APIs have security approval
