# Legacy API Decommission Rollback

## Purpose

Define how to restore legacy API traffic if a decommission step causes client
errors.

## Rollback Triggers

- Any important client receives 4xx/5xx errors after route disable.
- Production monitoring shows an error spike.
- A legacy `/api/...` client appears after the cutover window.
- Django replacement endpoint fails contract smoke tests.
- Operator or architecture reviewer calls a stop decision.

## Rollback Steps

1. Stop additional legacy route disable actions.
2. Restore the previous proxy/router rule for affected `/api/...` paths.
3. Keep Django `/api/v1/...` online for clients already migrated.
4. Run health and contract smoke tests.
5. Confirm request volume returns to normal.
6. Archive incident logs.
7. Create a corrective minor phase before retrying.

## Validation Commands

```powershell
python scripts\phase11_1_2_legacy_api_traffic_verification.py --log <production-log>
python scripts\phase11_1_3_api_decommission_gate.py
cd django_backend
python manage.py check
pytest
```

## Safety Notes

- Do not delete `backend/app.py` during rollback window.
- Do not delete compatibility matrices or route mapping docs.
- Do not change database schema as part of API decommission rollback.
- Keep audit logs available for architecture review.
