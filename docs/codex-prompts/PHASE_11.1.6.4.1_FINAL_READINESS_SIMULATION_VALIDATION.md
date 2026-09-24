# TASK: Phase 11.1.6.4.1 - Final Readiness Gate Simulation Validation

Project:

mecprecision-vietnam

====================================================
SAVE THIS PROMPT
====================================================

Save this task specification into:

docs/codex-prompts/

Filename:

PHASE_11.1.6.4.1_FINAL_READINESS_SIMULATION_VALIDATION.md

====================================================
CURRENT STATUS
====================================================

Completed:

Phase 11.1.6.5.4
Production Like Traffic Evidence Generation

Current simulation evidence:

COMPLETE_EVIDENCE_PACKAGE

Important:

This is STAGING_SIMULATION only.
It is NOT real production approval evidence.

====================================================
OBJECTIVE
====================================================

Validate the Final Readiness Gate workflow using production-like simulation
evidence.

Expected workflow decision for training:

READY_TO_EXECUTE_TRAINING

or:

BLOCKED_SAFELY

====================================================
IMPORTANT RULES
====================================================

DO NOT:

- execute shutdown
- disable Legacy API
- modify IIS
- modify proxy
- modify database
- modify production configuration

ONLY:

- run readiness validation
- generate reports
- verify gates

====================================================
READ DOCUMENTS
====================================================

Read:

docs/reviews/PHASE_11.1.6.5.4_TRAFFIC_SIMULATION_REVIEW.md

docs/reviews/PHASE_11.1.6.4_FINAL_READINESS_REPORT.md

docs/migration/LEGACY_API_DECOMMISSION_EXECUTION_RUNBOOK.md

docs/migration/LEGACY_API_DECOMMISSION_ROLLBACK.md

====================================================
TASK 1
====================================================

Run:

python scripts/phase11_1_6_4_final_readiness_gate.py

Evidence Gate expected:

PASS

Because:

- Legacy `/api/*` count = 0
- Django `/api/v1/*` count > 0
- Unknown clients = 0

====================================================
TASK 2
====================================================

Approval Gate:

If approval templates are unsigned, mark:

TRAINING_APPROVAL_SIMULATION

Do not modify real approval status.

====================================================
TASK 3
====================================================

Rollback Gate:

Confirm:

- rollback document exists
- rollback procedure exists
- rollback checkpoint exists

====================================================
TASK 4
====================================================

Monitoring Gate:

Confirm:

- monitoring checklist exists
- metrics are defined

====================================================
TASK 5
====================================================

Create report:

docs/reviews/PHASE_11.1.6.4.1_SIMULATION_READINESS_REPORT.md

Report must include:

- Evidence result
- Approval simulation result
- Rollback readiness
- Monitoring readiness
- Final decision
- Safety confirmation

====================================================
TASK 6
====================================================

Create tests:

tests/test_phase11_1_6_4_1_readiness_simulation.py

Test:

- simulation evidence accepted
- legacy traffic zero
- django traffic exists
- readiness report generated

====================================================
TESTING
====================================================

Run:

python scripts/phase11_1_6_4_final_readiness_gate.py

pytest tests/test_phase11_1_6_4_1_readiness_simulation.py

pytest

powershell -ExecutionPolicy Bypass -File scripts/run_migration_test.ps1

Expected:

READY_TO_EXECUTE_TRAINING

====================================================
GIT
====================================================

Branch:

migration/phase-11.1.6.4.1-readiness-simulation

Commit:

test: validate final readiness gate with simulation evidence

Tag:

phase-11.1.6.4.1-readiness-simulation-ready

====================================================
FINAL OUTPUT
====================================================

Return:

1. Branch
2. Commit hash
3. Evidence result
4. Approval simulation result
5. Rollback result
6. Monitoring result
7. Final decision
8. Review package
9. Git tag

FINAL STATUS:

READY_FOR_TRAINING_SHUTDOWN_VALIDATION

STOP.

DO NOT EXECUTE SHUTDOWN.
DO NOT START PHASE 11.2.
