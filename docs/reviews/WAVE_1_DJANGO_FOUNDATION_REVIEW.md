# Wave 1 Django Foundation Review

## Scope

Authentication, user/profile, and permission ownership moved into Django-owned foundation tables and services.

## Architecture Decision

New APIs are isolated under `/api/v1/foundation/` to preserve existing legacy-compatible `/api/v1/auth/` endpoints.

## Database Impact

Added managed Django tables:

- `foundation_permissions`
- `foundation_roles`
- `foundation_role_permissions`
- `foundation_users`
- `foundation_user_profiles`
- `foundation_auth_tokens`

Legacy tables were not deleted or modified.

## API Impact

New endpoints:

- `POST /api/v1/foundation/auth/login/`
- `POST /api/v1/foundation/auth/logout/`
- `GET, POST /api/v1/foundation/users/`
- `GET, PUT /api/v1/foundation/users/<id>/profile/`
- `GET /api/v1/foundation/permissions/roles/`
- `POST /api/v1/foundation/permissions/check/`

## Security Review

Tokens are stored as SHA-256 hashes. Unsupported legacy password hashes are imported as unusable passwords. No production deployment or legacy deletion was performed.

## Testing

- `python manage.py check`: PASS
- `python manage.py makemigrations --check --dry-run`: PASS
- `python manage.py migrate`: PASS
- `pytest tests/test_wave1_django_foundation.py`: PASS, 10 tests
- `pytest`: PASS, 198 tests
- `python ai-factory/run_ai_factory.py --wave django-wave-1`: PASS

## AI Factory Review

AI Factory completed and produced a human-review warning. The warning does not block implementation; it confirms production approval still requires a human reviewer.

## Decision

PASS_WITH_WARNING

Warning: legacy users with unsupported password hashes require password reset before Django-owned login.
