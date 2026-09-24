# API Security Review

## Phase

Phase 9.1 - Business API Cutover

## Permission Handling

The central API layer uses `ReadOnlyApiPermission`, which allows only safe HTTP
methods: `GET`, `HEAD`, and `OPTIONS`.

Write methods such as `POST`, `PUT`, `PATCH`, and `DELETE` are rejected before
any business service can perform work.

## Authentication Boundary

Login cutover is intentionally not implemented in Phase 9.1.

The auth preparation endpoints are read-only:

- `GET /api/v1/auth/profile/`
- `GET /api/v1/auth/permissions/`

The profile endpoint reads a demo admin ID from query/header for compatibility
testing only. It does not create sessions, issue tokens, refresh sessions, or
verify passwords.

## Sensitive Data Exposure

The auth profile serializer exposes only:

- ID
- full name
- email
- role
- active status
- 2FA enabled flag

It does not expose:

- password hashes
- reset tokens
- session IDs
- 2FA codes
- login attempt internals

## Readonly Enforcement

Database safety is preserved by:

- unmanaged `managed = False` models
- legacy database alias opened read-only
- repository boundaries
- service-only API access
- read-only permission class
- tests that reject write attempts

## Remaining Risks

- Production authentication must be reviewed separately before auth cutover.
- Business read APIs currently expose operational data and should be protected
  by real authentication before public deployment.
- Future write APIs require transaction tests and rollback strategy before
  approval.

## Recommendation

Approve Phase 9.1 only as an internal read-only API readiness layer. Do not
expose business endpoints publicly until authentication and authorization
cutover are approved.
