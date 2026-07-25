# API Security Hardening

## Authentication Boundary

Full authentication cutover is not implemented in Phase 9.2. Business APIs must
be treated as internal readiness APIs until real authentication and authorization
are approved.

## Permission Enforcement

`ReadOnlyApiPermission` allows only safe methods:

- `GET`
- `HEAD`
- `OPTIONS`

Unsafe methods are rejected:

- `POST`
- `PUT`
- `PATCH`
- `DELETE`

## Sensitive Fields

Auth preparation APIs must not expose:

- password hashes
- session IDs
- reset tokens
- 2FA codes
- raw login attempts

Tests verify that credential/session words do not appear in auth profile
payloads.

## Readonly Protection

Readonly protection is layered:

1. unmanaged legacy models
2. read-only legacy database connection
3. repository boundary
4. service boundary
5. read-only API permission
6. unsafe-method tests

## CSRF Considerations

Because Phase 9.2 APIs are read-only, CSRF risk is limited. Future authenticated
write APIs must define CSRF/session/token policy before implementation.

## Rate Limit Requirements

No rate limiting tool is deployed in Phase 9.2. Before public exposure, add:

- per-IP limit
- per-user limit after auth cutover
- burst protection
- logging for throttled requests

## Recommendation

Do not expose business API endpoints publicly until auth cutover, rate limiting
and monitoring are approved.
