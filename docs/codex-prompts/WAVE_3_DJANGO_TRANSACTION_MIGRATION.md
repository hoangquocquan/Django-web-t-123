# Wave 3 - Django Transaction Domain Ownership Migration

## Objective

Move transaction-domain ownership to Django for order management, workflow/approval, and transaction history.

## Scope

- Django-owned order headers and order items
- Django-owned workflow transitions and approvals
- Django-owned transaction history/audit records
- Inventory and customer integration through Wave 2 models
- Backward-compatible legacy quote read-only mappings

## DO NOT

- Migrate payment processing
- Remove the legacy transaction system
- Delete legacy database tables
- Modify external payment integrations
- Deploy production

## Implementation Tasks

- Create managed Django transaction domain models
- Create migrations and safe legacy quote/event seed logic
- Create transaction-safe services
- Create DRF endpoints under `/api/v1/orders/`, `/api/v1/workflows/`, and `/api/v1/transactions/`
- Protect APIs with Wave 1 foundation auth and permissions
- Add tests and migration reports

## Testing Requirements

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `python manage.py migrate`
- `pytest tests/test_wave3_transaction_domain.py`
- `pytest`
- `python ai-factory/run_ai_factory.py --wave django-wave-3`

## Expected Output

```text
DJANGO_TRANSACTION_WAVE_COMPLETE
```
