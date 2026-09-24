# Auth Migration Boundary

Phase: 3.1 - Database Mapping Hardening & ORM Preparation Rules  
Rule: Documentation only. No authentication migration.

## 1. Purpose

This document defines the security boundary for legacy authentication tables before Phase 4 read-only ORM models.

Authentication is one of the highest-risk migration areas. Phase 4 must not replace legacy auth.

## 2. Current Legacy Auth Tables

| Table | Purpose |
|---|---|
| `admin_users` | CMS admin accounts, password hash, role, status, avatar, 2FA flag |
| `admin_sessions` | Active admin sessions and device metadata |
| `login_attempts` | Login attempt tracking and lockout support |
| `password_reset_tokens` | Password reset token lifecycle |
| `admin_2fa_challenges` | 2FA challenge code lifecycle |
| `auth_email_outbox` | Email records for auth workflows |
| `admin_activity_logs` | Admin audit trail |

## 3. Phase 4 Rule

Phase 4 may map auth tables read-only only if needed for:

- admin dashboard counts,
- audit display,
- user list read-only display,
- relationship validation.

Phase 4 must not migrate auth behavior.

## 4. Do Not Do In Phase 4

Do not:

- replace Django auth,
- migrate password hashes,
- rewrite passwords,
- migrate sessions,
- change session cookie behavior,
- change password reset flow,
- change 2FA flow,
- change lockout rules,
- change role/permission checks,
- expose password/token/session fields in APIs.

## 5. Sensitive Fields

Sensitive fields include:

| Table | Fields |
|---|---|
| `admin_users` | `password_hash` |
| `admin_sessions` | `session_id`, `remote_addr`, `user_agent` |
| `password_reset_tokens` | `token` |
| `admin_2fa_challenges` | `challenge_id`, `code` |
| `login_attempts` | `remote_addr` |
| `auth_email_outbox` | `recipient`, `body` |

Rules:

- Do not expose sensitive fields in public APIs.
- Do not log sensitive values.
- Do not include raw tokens/password hashes in review screenshots or sample responses.

## 6. Future Dedicated Auth Migration Phase

Auth migration needs its own phase covering:

- password hasher compatibility,
- session migration strategy,
- account lock/unlock,
- reset token strategy,
- 2FA strategy,
- role/group/permission mapping,
- CSRF and admin write protection,
- audit logging,
- rollback to legacy login.

## 7. Recommended Future Direction

Initial recommended direction:

- map legacy auth tables read-only,
- build permission matrix,
- implement compatibility password hasher only after review,
- keep legacy auth fallback until Django auth is proven,
- migrate auth last among core admin capabilities.

## 8. Risk

Risk level:

```text
High
```

Reason:

- auth mistakes can lock admins out,
- password/session mistakes can become security vulnerabilities,
- permission mistakes can expose admin functionality.
