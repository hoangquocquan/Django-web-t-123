# Phase 11.1.6 Operations Handover

## Runbook

Primary runbook:

`docs/migration/LEGACY_API_DECOMMISSION_EXECUTION_RUNBOOK.md`

Operational note: hardening introduced explicit decisions:

- Training: `READY_TO_EXECUTE_TRAINING`
- Production: `READY_TO_EXECUTE_PRODUCTION`
- Blocked: `BLOCKED_SAFELY`

Use the explicit production decision before any real routing work.

## Evidence Collection

Required production evidence must be collected from real production traffic and
must include:

- IIS W3C logs
- CSV API evidence export
- collection period
- environment = `production`
- simulation = `false`
- source
- approved_by

Simulation evidence is allowed for training only and is stored as:

`docs/migration/production_evidence/reports/SIMULATION_PRODUCTION_EVIDENCE_REPORT.json`

## Validation Steps

Training validation:

```powershell
python scripts\phase11_1_6_4_1_readiness_simulation.py
```

Production evidence validation:

```powershell
python scripts\phase11_1_6_5_production_evidence_validator.py
python scripts\phase11_1_6_pre_shutdown_validation.py
python scripts\phase11_1_6_4_final_readiness_gate.py --readiness-mode production
```

Expected current production result:

```text
BLOCKED_SAFELY
```

## Monitoring

During a future approved shutdown window, monitor:

- `/api/*` request attempts
- `/api/v1/*` request volume
- unknown clients
- 4xx and 5xx rates
- API latency
- customer-facing contact and quotation flows

## Rollback Procedure

Rollback document:

`docs/migration/LEGACY_API_DECOMMISSION_ROLLBACK.md`

Rollback steps:

1. Stop additional route-disable actions.
2. Restore previous `/api/*` router/proxy rule.
3. Keep `/api/v1/*` online.
4. Run smoke tests.
5. Monitor errors, latency and traffic.
6. Record rollback evidence.

## Emergency Response

Stop or roll back if:

- an important client fails after route changes
- unknown clients appear
- error rate increases
- Django `/api/v1/*` smoke tests fail
- monitoring is unavailable
- rollback owner cannot be reached

## Current Operations Status

`APPROVED_FOR_TRAINING`

`BLOCKED_FOR_PRODUCTION`
