# Wave 1 User/Profile Report

## Ownership Result

Django now owns new foundation user/profile writes through:

- `FoundationUserService.create_user`
- `FoundationUserService.update_profile`
- `/api/v1/foundation/users/`
- `/api/v1/foundation/users/<id>/profile/`

## Database Tables

New managed tables:

- `foundation_users`
- `foundation_user_profiles`

Legacy table preserved:

- `admin_users`

## Data Migration Approach

Migration `foundation.0002_seed_foundation_from_legacy` reads legacy `admin_users` in SQLite read-only mode and creates matching Django-owned users with `legacy_admin_id`.

The migration is idempotent through `update_or_create`.

## Write Ownership

New user creation and profile updates go to Django tables only. Legacy tables are not updated.

## Compatibility

Legacy admin user models remain `managed = False`, and legacy repositories continue reading through the `legacy` database alias.
