# TASK: Phase 11.1.6.8 - Training Legacy API Shutdown Execution

Project:

mecprecision-vietnam

## Objective

Execute Legacy API shutdown simulation in the training environment.

Training status:

`READY_TO_EXECUTE_TRAINING`

Production status:

`BLOCKED_SAFELY`

## Scope

Practice the complete decommission lifecycle:

- before: Legacy `/api/*` active
- after: Legacy `/api/*` disabled in training state
- replacement `/api/v1/*` remains active
- rollback restores Legacy `/api/*` in training state

## Do Not

- Do not shut down real production.
- Do not modify external systems.
- Do not change real IIS production.
- Do not affect real users.
- Do not execute production shutdown.

## Allowed

- Execute training shutdown only.
- Validate migration flow.
- Test rollback.
- Generate review reports.

## Required Files

- scripts/phase11_1_6_8_training_legacy_shutdown.py
- scripts/phase11_1_6_8_training_rollback.py
- docs/reviews/PHASE_11.1.6.8_SHUTDOWN_RESULT.json
- docs/reviews/PHASE_11.1.6.8_TRAFFIC_VERIFICATION.md
- docs/reviews/PHASE_11.1.6.8_ROLLBACK_RESULT.md
- docs/reviews/PHASE_11.1.6.8_TRAINING_SHUTDOWN_REPORT.md
- tests/test_phase11_1_6_8_training_shutdown.py

## Expected Status

`TRAINING_SHUTDOWN_SUCCESS`

Production remains:

`BLOCKED_SAFELY`
