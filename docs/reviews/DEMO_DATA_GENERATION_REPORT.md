# Demo Data Generation Report

## Status

MEC_DEMO_DATA_READY

## Generated Data Areas

- Foundation users, roles, and permissions.
- Business customers and products.
- CRM profiles, interactions, notes, tasks, and timeline events.
- Sales leads, opportunities, quotations, lines, follow-ups, and activities.
- Transaction orders, order items, status history, approvals, and audit events.
- Knowledge documents prepared for AI search.

## Safety

All generated records are fictional and tagged with demo identifiers such as `DEMO`, `[DEMO]`, `demo_data=true`, or `demo.mecprecision.local`.

Cleanup is handled by:

```powershell
python django_backend/manage.py clear_demo_data
```

## Local Generation Result

- Users: 7
- Customers: 500
- Products: 200
- Warehouses: 2
- Leads: 1000
- Opportunities: 300
- Quotations: 500
- Orders: 200
- Knowledge documents: 100
- Sales activities: 4500
- CRM interactions: 500
- Total activity history: 5000
- Pipeline value: `23428927.00`

## Validation

- Django system check: PASS
- Focused test: `pytest tests/test_demo_data_generation.py` PASS, 5 passed
- Full test suite: PASS, 337 passed
