# Wave 1 - Django Foundation Ownership Migration

## Objective

Move foundation ownership from the legacy backend to Django for authentication, user/profile management, and permissions.

## Scope

- Django-owned authentication token lifecycle
- Django-owned foundation users and profiles
- Django-owned roles and permissions
- Backward-compatible legacy auth read-only access
- Tests and review evidence

## DO NOT

- Remove the legacy backend
- Delete old database tables
- Migrate unrelated business modules
- Deploy production
- Disable legacy authentication before approval

## Implementation Tasks

- Create managed Django foundation models
- Create migrations and safe seed logic from legacy admin users
- Create service layer for auth, users, and permissions
- Create DRF endpoints under `/api/v1/foundation/`
- Preserve existing `/api/v1/auth/` compatibility endpoints
- Add automated tests

## Testing Requirements

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py migrate`
- `pytest tests/test_wave1_django_foundation.py`
- `pytest`
- `python ai-factory/run_ai_factory.py --wave django-wave-1`

## Expected Output

```text
DJANGO_FOUNDATION_WAVE_COMPLETE
```
