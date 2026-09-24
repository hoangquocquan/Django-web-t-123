# Phase 8 - Authentication Migration

## Objective

Design and implement authentication migration only after read-only auth mapping and security review are approved.

## Scope

- admin users
- sessions
- login attempts
- password reset tokens
- 2FA challenges
- activity logs
- permission mapping

## Dependencies

- auth migration boundary approved
- security review approved
- read-only auth table mapping approved
- rollback strategy approved

## DO NOT

- Do not overwrite password hashes without approval
- Do not remove legacy login fallback
- Do not change session cookie behavior silently
- Do not expose tokens/password hashes
- Do not migrate auth together with unrelated modules

## Implementation Tasks

- Confirm password hash compatibility
- Define permission matrix
- Map legacy roles to Django permission model
- Implement auth compatibility layer if approved
- Add login/logout/reset/session tests
- Add rollback plan

## Testing Requirements

- `python manage.py check`
- `pytest`
- login/logout tests
- password reset tests
- account lock/unlock tests
- session expiration tests
- permission matrix tests

## Git Requirements

- Create phase branch
- Create checkpoint commit
- Commit final implementation
- Create phase tag

## Review Package Requirements

- `docs/reviews/PHASE_8_CHANGESET.patch`
- `docs/reviews/PHASE_8_REVIEW_SUMMARY.md`

## Expected Output

- Auth migration package
- Security review notes
- Passing auth tests
- Review package ready
