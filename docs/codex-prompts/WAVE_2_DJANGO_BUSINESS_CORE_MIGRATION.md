# Wave 2 - Django Business Core Ownership Migration

## Objective

Move core business ownership to Django for Product, Customer, and Inventory.

## Scope

- Django-owned product records and writes
- Django-owned customer records and writes
- Django-owned inventory warehouses, balances, and stock transactions
- Backward-compatible legacy read-only catalog and CRM mappings
- Tests and AI Factory evidence

## DO NOT

- Remove the legacy backend
- Delete old database tables
- Migrate payment or transaction domains
- Deploy production
- Disable compatibility layers

## Implementation Tasks

- Create managed Django business core models
- Create migrations and safe legacy seed logic
- Create service layer with inventory transaction safety
- Create DRF endpoints under `/api/v1/business/` and `/api/v1/inventory/`
- Protect APIs with Wave 1 foundation auth and permissions
- Add tests and migration reports

## Testing Requirements

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py migrate`
- `pytest tests/test_wave2_business_core.py`
- `pytest`
- `python ai-factory/run_ai_factory.py --wave django-wave-2`

## Expected Output

```text
DJANGO_BUSINESS_CORE_WAVE_COMPLETE
```
