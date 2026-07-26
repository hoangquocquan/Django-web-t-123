# TASK: Phase 11.1.6.6 - Full Migration Readiness Audit

Project:

mecprecision-vietnam

====================================================
SAVE THIS PROMPT
====================================================

Save this task specification into:

docs/codex-prompts/

Filename:

PHASE_11.1.6.6_FULL_MIGRATION_READINESS_AUDIT.md

====================================================
CURRENT STATUS
====================================================

Completed:

Phase 11.1.6.1
Evidence And Approval Framework

Phase 11.1.6.2
Evidence Validation Framework

Phase 11.1.6.3
Approval Package Framework

Phase 11.1.6.4
Final Readiness Gate

Phase 11.1.6.5
Production Evidence Acquisition Framework

Phase 11.1.6.5.4
Production Like Traffic Simulation

Phase 11.1.6.4.1
Final Readiness Simulation Validation

Current result:

READY_TO_EXECUTE_TRAINING

IMPORTANT:

This is training simulation only.

Production shutdown must remain blocked until:

- real IIS production evidence exists
- real approvals exist

====================================================
OBJECTIVE
====================================================

Perform a complete audit of Phase 11.1.6.

Verify:

1. Simulation evidence is not treated as production evidence.
2. Production shutdown cannot accidentally execute.
3. Readiness status files are correctly separated.
4. All governance documents are consistent.

====================================================
IMPORTANT RULES
====================================================

DO NOT:

- execute shutdown
- disable Legacy API
- modify IIS
- modify proxy
- modify database
- change routes

ONLY:

- audit
- review
- classify
- report

====================================================
READ REQUIRED DOCUMENTS
====================================================

Read all:

docs/reviews/PHASE_11.1.6*

docs/migration/phase11_1_6_execution/*

docs/migration/production_evidence/*

scripts/phase11_1_6*

tests/test_phase11_1_6*

====================================================
TASK 1
====================================================

Create Phase Inventory.

Create:

docs/reviews/PHASE_11.1.6_PHASE_INVENTORY.md

Include:

Phase

Purpose

Status

Evidence type:

REAL_PRODUCTION

or

TRAINING_SIMULATION

Approval type:

REAL_APPROVAL

or

SIMULATION_APPROVAL

Risk level

====================================================
TASK 2
====================================================

Audit Readiness Status Files.

Check:

FINAL_READINESS_STATUS.json

FINAL_READINESS_SIMULATION_STATUS.json

Verify:

No simulation status overwrites production status.

====================================================
TASK 3
====================================================

Audit Evidence Separation.

Check:

Production evidence folder

Simulation evidence folder

Expected:

Clearly separated.

====================================================
TASK 4
====================================================

Audit Shutdown Protection.

Verify:

Shutdown scripts require:

REAL evidence

REAL approval

NOT simulation

If missing:

Report as risk.

====================================================
TASK 5
====================================================

Create Risk Report.

Create:

docs/reviews/PHASE_11.1.6_READINESS_AUDIT_REPORT.md

Include:

Completed items

Simulation items

Production blockers

Security risks

Shutdown risks

Recommendation

Possible results:

SAFE_TO_CONTINUE_TRAINING

BLOCKED_FOR_PRODUCTION

====================================================
TASK 6
====================================================

Create Audit Test.

Create:

tests/test_phase11_1_6_6_readiness_audit.py

Test:

- simulation cannot unlock production
- missing production evidence blocks shutdown
- missing approval blocks shutdown
- status separation works

====================================================
TASK 7
====================================================

Testing.

Run:

pytest tests/test_phase11_1_6_6_readiness_audit.py

pytest

powershell -ExecutionPolicy Bypass -File scripts/run_migration_test.ps1

====================================================
GIT REQUIREMENTS
====================================================

Create branch:

migration/phase-11.1.6.6-readiness-audit

Commit:

audit: verify legacy api shutdown readiness separation

Create tag:

phase-11.1.6.6-readiness-audit-ready

====================================================
FINAL OUTPUT
====================================================

Return:

1. Branch
2. Commit hash
3. Audit report location
4. Simulation status
5. Production readiness status
6. Shutdown safety result
7. Testing result
8. Git tag

FINAL STATUS:

WAITING_FOR_ARCHITECT_REVIEW

STOP.

DO NOT EXECUTE SHUTDOWN.
DO NOT START PHASE 11.2.
