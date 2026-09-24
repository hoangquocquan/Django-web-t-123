# Auth Migration Limitations

## Scope In Phase 8

Phase 8 implements read-only authentication mapping and compatibility analysis in Django.

Mapped tables:

- `admin_users`
- `admin_sessions`
- `login_attempts`
- `password_reset_tokens`
- `admin_2fa_challenges`
- `admin_activity_logs`

## What Is Intentionally Not Included

- No password hash overwrite.
- No legacy login fallback removal.
- No silent session cookie behavior change.
- No token or password hash exposure through API.
- No unrelated module migration.
- No write-enabled login/logout/reset endpoints.

## Password Hash Boundary

Legacy authentication supports:

- `pbkdf2_sha256$...` hashes
- older salted SHA-256 legacy hashes

Phase 8 only detects hash format and upgrade requirement. It does not verify real passwords and does not upgrade stored hashes.

Observed current data:

- PBKDF2 hashes: 3
- Legacy SHA-256 hashes: 2

## Session Boundary

`admin_sessions` is mapped read-only.

Phase 8 can inspect expiration state but must not update `last_seen_at`, delete expired sessions or create new session rows.

## Token Boundary

`password_reset_tokens.token` and `admin_2fa_challenges.code` are sensitive.

Phase 8 does not expose token/code values through a public service or API. Repository access is internal only for validation and relationship checks.

## Future Readiness

Phase 8 prepares future auth migration work for:

- Django-compatible admin identity mapping,
- permission matrix enforcement,
- login compatibility testing,
- password reset migration,
- session migration,
- rollback-safe cutover planning.
