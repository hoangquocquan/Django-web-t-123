# Auth Rollback Plan

## Purpose

Authentication migration has high operational risk. A rollback plan must exist before any write-enabled auth cutover.

## Phase 8 State

Phase 8 is read-only.

Rollback for Phase 8 is simple:

- remove Django auth read-only app from deployment,
- keep legacy backend auth unchanged,
- keep existing SQLite auth tables untouched.

## Future Cutover Rollback

Before enabling Django write/auth flows:

1. Backup SQLite database.
2. Export admin users, sessions and token metadata counts.
3. Keep legacy login route available.
4. Keep legacy password hash verifier available.
5. Define session fallback behavior.

## Rollback Triggers

Rollback if:

- admins cannot log in,
- active sessions become invalid unexpectedly,
- reset password flow fails,
- account lock/unlock state diverges,
- permission matrix behavior changes unexpectedly,
- security review finds token/hash exposure.

## Rollback Actions

- Disable Django auth routes.
- Re-enable legacy login route as primary.
- Preserve existing `admin_users.password_hash` values.
- Preserve existing session cookie behavior.
- Invalidate only sessions created by failed cutover if needed.
- Review audit logs before retry.

## Non-Negotiable Rules

- Never bulk overwrite password hashes without verified backup.
- Never delete legacy sessions without explicit approval.
- Never remove legacy login fallback during first cutover.
