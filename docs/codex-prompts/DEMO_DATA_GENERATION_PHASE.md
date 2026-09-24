# Demo Data Generation Phase

## Objective

Generate realistic fictional enterprise demo data for full MEC Precision platform testing.

## Scope

- Foundation users, roles, and permissions.
- Business customers and products.
- CRM interactions, notes, tasks, and timeline.
- Sales leads, opportunities, quotations, and activities.
- Transaction orders and workflow records.
- Knowledge documents for AI search.
- Cleanup command for demo data only.

## DO NOT

- Do not use real customer information.
- Do not modify production data.
- Do not change business logic.
- Do not deploy.

## Commands

Generate full demo data:

```powershell
python django_backend/manage.py generate_demo_data
```

Generate compact demo data:

```powershell
python django_backend/manage.py generate_demo_data --small
```

Clear generated demo data:

```powershell
python django_backend/manage.py clear_demo_data
```

## Testing

- `python django_backend/manage.py check`
- `pytest tests/test_demo_data_generation.py`
- `pytest`
