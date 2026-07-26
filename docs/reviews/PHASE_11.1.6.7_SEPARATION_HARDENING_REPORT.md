# Phase 11.1.6.7 Separation Hardening Report

## Problem

Phase 11.1.6.6 found that simulation evidence could be stored with names that
look like real production evidence. This can confuse operators and reviewers
during Legacy API shutdown readiness checks.

## Risk

Before this hardening phase, a simulation report named like production evidence
could be manually passed to a production gate. If approval overrides were also
provided, a reviewer could misunderstand the result.

## Changes

- Added `docs/migration/EVIDENCE_CLASSIFICATION_STANDARD.md`.
- Renamed the simulation report from
  `REAL_PRODUCTION_EVIDENCE_REPORT.json` to
  `SIMULATION_PRODUCTION_EVIDENCE_REPORT.json`.
- Marked simulation evidence as `TRAINING_ONLY` and `ready_for_shutdown = false`.
- Hardened `scripts/phase11_1_6_5_production_evidence_validator.py` so
  simulation evidence can never return `COMPLETE_EVIDENCE_PACKAGE`.
- Hardened `scripts/phase11_1_6_4_final_readiness_gate.py` with separate
  production and training readiness modes.
- Hardened pre-shutdown and final evidence validators so simulation evidence
  cannot unlock production shutdown.
- Added regression tests for production/simulation separation.

## Before / After

| Area | Before | After |
| --- | --- | --- |
| Simulation report name | `REAL_PRODUCTION_EVIDENCE_REPORT.json` | `SIMULATION_PRODUCTION_EVIDENCE_REPORT.json` |
| Simulation evidence status | `COMPLETE_EVIDENCE_PACKAGE` | `TRAINING_ONLY` |
| Production gate decision | Could be confused by manually supplied simulation evidence | `BLOCKED_SAFELY` for simulation |
| Training gate decision | Custom simulation wrapper | Explicit `READY_TO_EXECUTE_TRAINING` mode |
| Production success decision | `READY_TO_EXECUTE` | `READY_TO_EXECUTE_PRODUCTION` |

## Validation

Expected decisions:

| Scenario | Expected Decision |
| --- | --- |
| Simulation evidence in production mode | `BLOCKED_SAFELY` |
| Simulation evidence in training mode | `READY_TO_EXECUTE_TRAINING` |
| Real production evidence with metadata and approvals | `READY_TO_EXECUTE_PRODUCTION` |
| Missing metadata | `BLOCKED_SAFELY` |
| Missing environment | `BLOCKED_SAFELY` |

## Final Status

`SAFE_TO_CONTINUE_TRAINING`

`BLOCKED_FOR_PRODUCTION_UNTIL_REAL_EVIDENCE_AND_APPROVALS`

No shutdown was executed. Legacy API was not disabled. IIS, proxy, routes and
database were not modified.
