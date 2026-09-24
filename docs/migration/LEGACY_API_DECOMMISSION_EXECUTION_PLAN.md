# Legacy API Decommission Execution Plan

## Phase

Phase 11.1.3 - Legacy API Decommission Execution

## Current Decision

```text
BLOCKED_SAFELY
```

The previous traffic verification phase did not receive production traffic
logs. Because there is no proof that legacy `/api/...` usage is zero, legacy API
routes must stay active.

## Execution Gate

Run:

```powershell
python scripts\phase11_1_3_api_decommission_gate.py
```

Default result in local/demo environment:

```text
BLOCKED_SAFELY
```

Required evidence before approval:

| Evidence | Environment variable |
|---|---|
| Architecture/business approval | `PHASE11_1_3_APPROVAL=approved` |
| Approval identifier | `PHASE11_1_3_APPROVAL_ID=<approval-id>` |
| Explicit operator confirmation | `PHASE11_1_3_OPERATOR_CONFIRMATION=I_UNDERSTAND_LEGACY_API_DECOMMISSION_RISK` |
| Rollback plan is ready | `PHASE11_1_3_ROLLBACK_READY=approved` |
| Rollback owner exists | `PHASE11_1_3_ROLLBACK_OWNER=<owner>` |
| Production traffic log path | `PHASE11_1_2_LOG_PATHS=<log-path>` |

## Controlled Disable Workflow

Run:

```powershell
python scripts\phase11_1_3_disable_legacy_api.py
```

The script only returns a route disable plan. It does not edit `backend/app.py`,
does not remove compatibility code and does not change the database.

## Manual Execution Order

1. Archive production access logs for the approved observation window.
2. Run the Phase 11.1.2 traffic verification script against those logs.
3. Run the Phase 11.1.3 gate.
4. Confirm `READY_FOR_DECOMMISSION_EXECUTION`.
5. Apply proxy/router rules in the approved production window.
6. Keep `/api/v1/...` endpoints active.
7. Monitor errors, request volume and unknown clients.
8. Roll back immediately if any stop condition appears.

## Stop Conditions

- Any legacy `/api/...` request still appears in production logs.
- Unknown clients are detected.
- Approval ID is missing.
- Rollback owner is missing.
- Rollback plan file is missing.
- Django API smoke tests fail.
- Error rate increases after route changes.

## Impact

| Area | Impact |
|---|---|
| Legacy code | No code is deleted |
| Django API | `/api/v1/...` remains active |
| Database | No schema or data change |
| Rollback | Route/proxy mapping can be restored |

## Phase 11.1.5 Production Shutdown Readiness Update

### Owner

```text
PENDING
```

Final shutdown owner, rollback owner and business owner must be assigned before
production route changes are allowed.

### Timeline

1. Collect 7-30 days of production traffic evidence.
2. Run `scripts\phase11_1_4_production_traffic_evidence.py`.
3. Run `scripts\phase11_1_5_shutdown_readiness_check.py`.
4. Obtain technical and business approval.
5. Execute route shutdown only during the approved maintenance window.
6. Monitor post-shutdown traffic and errors.

### Validation Steps

```powershell
python scripts\phase11_1_5_shutdown_readiness_check.py
cd django_backend
python manage.py check
pytest
```

Required readiness result:

```text
READY_FOR_LEGACY_API_SHUTDOWN
```

### Rollback Steps

Use:

```text
docs/migration/LEGACY_API_DECOMMISSION_ROLLBACK.md
```

Minimum rollback actions:

1. Restore the previous proxy/router rule for `/api/...`.
2. Keep Django `/api/v1/...` online.
3. Run API smoke tests.
4. Confirm request volume and error rate return to normal.
5. Record the incident and create a corrective minor phase.

### Post Shutdown Monitoring

Track:

- `/api/...` request attempts
- `/api/v1/...` request volume
- unknown clients
- 4xx and 5xx error rate
- contact and quotation form success rate
- API latency

Current status:

```text
KEEP_LEGACY_API_ACTIVE
```
