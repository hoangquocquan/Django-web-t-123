# Authentication Hardening

## Current State

Legacy backend:

- supports admin login/logout
- uses password hashing compatibility and PBKDF2 upgrade path
- creates random session IDs
- supports password reset tokens
- supports CSRF token injection/verification for admin forms
- tracks session expiry

Django backend:

- exposes read-only auth compatibility endpoints
- does not issue sessions or tokens
- does not perform final login cutover
- defers password hashes from default admin reads

## User Authentication Flow

Current production-sensitive authentication still belongs to the legacy backend.
Django is currently a compatibility/read layer for profile and permissions.

## Password Handling

Current strengths:

- PBKDF2-compatible hash support exists
- legacy hashes can be identified for upgrade
- API profile response does not expose password hashes

Issues:

- legacy local default salt exists for development
- password policy is still managed in legacy settings/data
- production auth cutover needs a dedicated phase

## Session Management

Current strengths:

- random session IDs use Python `secrets`
- session TTL exists
- cookies are `HttpOnly` and `SameSite=Lax` in legacy responses

Issues:

- production cookie `Secure` flag depends on deployment path
- session storage remains legacy SQLite
- multi-device/session invalidation needs production review

## Token Handling

Reset and 2FA token data exists in legacy tables and must not be exposed by
APIs, logs or review artifacts.

## API Authentication

Django `/api/v1/auth/profile/` and `/api/v1/auth/permissions/` are
compatibility/read endpoints. They must not be used as final production login
APIs.

## Recommendations

1. Design a final Django auth cutover phase.
2. Replace demo/local defaults with secret-manager backed values.
3. Add login throttling/rate limiting in production infrastructure.
4. Add secret redaction tests for logs and API responses.
5. Add formal session revocation and token rotation procedures.

## Implementation Status

| Item | Status |
| --- | --- |
| Sensitive auth field non-exposure tests | Implemented |
| Read-only auth compatibility | Implemented |
| Final Django login cutover | Pending |
| Production session/cookie policy | Pending security review |
| Secret-manager integration | Pending |
