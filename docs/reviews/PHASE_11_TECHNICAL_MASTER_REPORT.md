# Phase 11 Technical Master Report

## Legacy Architecture

The legacy Python backend remains the owner of legacy `/api/*` behavior. It is
kept available as the rollback path and compatibility surface until the final
production gate returns `READY_TO_EXECUTE_PRODUCTION`.

## New Architecture

Django exposes the replacement API surface under `/api/v1/*`. Replacement
coverage was documented and validated in Phase 11.1.1, including contact,
quotation, catalog, CMS, AI/demo and documentation endpoints.

## API Migration

| Legacy Surface | Replacement Surface | Status |
| --- | --- | --- |
| `/api/*` | `/api/v1/*` | Replacement coverage complete |
| Legacy write APIs | Django write-intent contracts | Migration-safe, no legacy DB mutation |
| Legacy OpenAPI/demo endpoints | Django replacement contracts | Complete |

## Traffic Migration

Production traffic migration is not proven yet. Current real production traffic
report remains incomplete, while simulation traffic is classified as
`STAGING_SIMULATION_EVIDENCE` and `TRAINING_ONLY`.

## Evidence Strategy

Evidence must follow `docs/migration/EVIDENCE_CLASSIFICATION_STANDARD.md`:

- production evidence: `REAL_PRODUCTION_EVIDENCE`, `simulation = false`
- simulation evidence: `STAGING_SIMULATION_EVIDENCE`, `TRAINING_ONLY`
- development/test evidence: never unlocks production

## Validation Strategy

Required validation chain:

```powershell
python scripts\phase11_1_6_5_production_evidence_validator.py
python scripts\phase11_1_6_pre_shutdown_validation.py
python scripts\phase11_1_6_4_final_readiness_gate.py --readiness-mode production
```

Training validation:

```powershell
python scripts\phase11_1_6_4_1_readiness_simulation.py
```

## Rollback Strategy

Rollback restores previous router/proxy behavior for `/api/*` while keeping
Django `/api/v1/*` active. No database rollback is required for route-level
decommission because this phase does not change schema or data.

## Shutdown Strategy

Shutdown may only occur after:

1. real production evidence is complete,
2. legacy `/api/*` traffic is zero,
3. Django `/api/v1/*` traffic is observed,
4. unknown clients are zero,
5. technical/business/rollback/maintenance/monitoring approvals are complete,
6. final gate returns `READY_TO_EXECUTE_PRODUCTION`.

Current shutdown strategy result:

`BLOCKED_SAFELY`
