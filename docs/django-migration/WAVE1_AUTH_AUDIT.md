# Wave 1 Auth Audit

## Current Legacy Flow

Legacy authentication is stored in `backend/database/mecprecision.sqlite` with `admin_users`, `admin_sessions`, `login_attempts`, `password_reset_tokens`, and `admin_2fa_challenges`.

The Django `apps.accounts` app maps those tables as unmanaged read-only models. Repositories use the `legacy` database alias and `LegacyReadOnlyModel` blocks accidental writes.

## Django Ownership Added

Wave 1 adds the managed `apps.foundation` app:

- `FoundationUser`
- `FoundationUserProfile`
- `FoundationAuthToken`
- `FoundationRole`
- `FoundationPermission`
- `FoundationRolePermission`

The new auth ownership is implemented by `FoundationAuthService`.

## Token Handling

Django now creates hashed bearer tokens in `foundation_auth_tokens`. Raw tokens are returned only once during login and only the SHA-256 hash is stored.

## Password Handling

Supported Django hashes from legacy users are copied. Unsupported legacy hashes are imported as unusable passwords so the account remains visible but must reset/change password before login.

## Backward Compatibility

Legacy `/api/v1/auth/profile/` and `/api/v1/auth/permissions/` remain unchanged and read-only.

New Django-owned APIs are isolated under `/api/v1/foundation/`.

## Risk

Some imported users with legacy SHA-256-style hashes cannot log in until password reset because Django does not verify those old hashes in this wave.
