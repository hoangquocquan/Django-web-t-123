# Auth Security Review

## Scope

This review covers Phase 8 read-only authentication migration.

## Sensitive Data

Sensitive fields:

- `admin_users.password_hash`
- `password_reset_tokens.token`
- `admin_2fa_challenges.code`
- `admin_sessions.session_id`

## Current Controls

- No API endpoints were created.
- Admin user repository defers `password_hash` by default.
- Auth compatibility service returns safe profile data without password hashes.
- Password hash inspector returns only algorithm metadata.
- Session expiration checks do not update `last_seen_at`.
- Reset token and 2FA checks are read-only state checks.

## Password Hash Compatibility

Legacy auth supports:

- PBKDF2-HMAC-SHA256 in format `pbkdf2_sha256$iterations$salt$hash`
- older salted SHA-256 hashes

Current data contains both formats.

Recommendation:

- Keep legacy fallback until all legacy hashes are upgraded through an approved login or reset flow.
- Do not bulk rewrite password hashes.
- Do not log password hashes or reset tokens.

## Session Risk

Legacy session rows are stored in SQLite.

Risk:

- Migrating sessions incorrectly can log out active admins or leave stale sessions active.

Recommendation:

- Future cutover must decide whether to honor legacy sessions, force re-login or run dual-session validation.

## Reset Token Risk

Reset token rows contain bearer secrets.

Recommendation:

- Never expose token values in admin/API lists.
- Only accept token value as inbound credential in a dedicated reset flow.
- Mark token used inside a transaction only after password update succeeds.

## 2FA Risk

2FA challenge codes are one-time secrets.

Recommendation:

- Future migration must add expiry policy if not already enforced at service level.
- Never return challenge codes to frontend after creation.

## Result

Phase 8 is acceptable as a read-only compatibility layer.

Write-enabled auth migration requires separate approval.
