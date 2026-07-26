# TASK: Phase 11.1.6.7 - Production Simulation Separation Hardening

Project:

mecprecision-vietnam

====================================================
SAVE THIS PROMPT
====================================================

Save this task specification into:

docs/codex-prompts/

Filename:

PHASE_11.1.6.7_PRODUCTION_SIMULATION_SEPARATION_HARDENING.md

====================================================
CURRENT STATUS
====================================================

Completed:

Phase 11.1.6.6
Full Migration Readiness Audit

Audit Result:

SAFE_TO_CONTINUE_TRAINING

BLOCKED_FOR_PRODUCTION

Issue Found:

Simulation evidence can have filenames similar to production evidence.

Risk:

Training artifacts may be misunderstood as real production evidence.

====================================================
OBJECTIVE
====================================================

Harden separation between:

TRAINING_SIMULATION

and

REAL_PRODUCTION

Ensure readiness gates cannot confuse these states.

====================================================
IMPORTANT RULES
====================================================

DO NOT:

- execute shutdown
- disable Legacy API
- modify IIS
- modify proxy
- modify database

ONLY:

- improve safety controls
- improve naming
- improve validation
- improve documentation

====================================================
READ REQUIRED DOCUMENTS
====================================================

Read:

docs/reviews/PHASE_11.1.6_READINESS_AUDIT_REPORT.md

docs/reviews/PHASE_11.1.6.4.1_SIMULATION_READINESS_REPORT.md

docs/reviews/PHASE_11.1.6.6_REVIEW_SUMMARY.md

docs/migration/phase11_1_6_execution/FINAL_READINESS_STATUS.json

docs/migration/phase11_1_6_execution/FINAL_READINESS_SIMULATION_STATUS.json

====================================================
TASK 1
====================================================

Create Evidence Classification Standard.

Create:

docs/migration/EVIDENCE_CLASSIFICATION_STANDARD.md

Include:

Evidence types:

REAL_PRODUCTION_EVIDENCE

STAGING_SIMULATION_EVIDENCE

DEVELOPMENT_TEST_EVIDENCE

Required metadata:

environment

simulation

source

collection_period

approved_by

====================================================
TASK 2
====================================================

Update Simulation Evidence Naming.

Rename or create simulation-safe files:

Before:

REAL_PRODUCTION_EVIDENCE_REPORT.json

After:

SIMULATION_PRODUCTION_EVIDENCE_REPORT.json

Add metadata:

{
 "simulation": true,
 "environment": "STAGING_SIMULATION"
}

====================================================
TASK 3
====================================================

Create Production Evidence Validator Hardening.

Update:

scripts/phase11_1_6_5_production_evidence_validator.py

Rules:

If:

simulation=true

then result:

TRAINING_ONLY

Never:

COMPLETE_EVIDENCE_PACKAGE

for production gate.

====================================================
TASK 4
====================================================

Create Readiness Gate Protection.

Update:

scripts/phase11_1_6_4_final_readiness_gate.py

Rules:

Simulation:

READY_TO_EXECUTE_TRAINING

Production:

READY_TO_EXECUTE_PRODUCTION

Never allow:

simulation=true

to produce:

READY_TO_EXECUTE_PRODUCTION

====================================================
TASK 5
====================================================

Create Safety Report.

Create:

docs/reviews/PHASE_11.1.6.7_SEPARATION_HARDENING_REPORT.md

Include:

Problem

Risk

Changes

Before/After

Validation

Final status

====================================================
TASK 6
====================================================

Create Tests.

Create:

tests/test_phase11_1_6_7_simulation_separation.py

Test:

- simulation evidence rejected for production
- simulation returns training status
- production evidence accepted
- metadata required
- missing environment blocked

====================================================
TASK 7
====================================================

Testing.

Run:

pytest tests/test_phase11_1_6_7_simulation_separation.py

pytest

powershell -ExecutionPolicy Bypass -File scripts/run_migration_test.ps1

Expected:

PASS

Expected decisions:

Simulation:

READY_TO_EXECUTE_TRAINING

Production:

READY_TO_EXECUTE_PRODUCTION

====================================================
GIT REQUIREMENTS
====================================================

Create branch:

migration/phase-11.1.6.7-simulation-separation-hardening

Commit:

security: separate training simulation from production readiness

Create tag:

phase-11.1.6.7-separation-hardening-ready

====================================================
FINAL OUTPUT
====================================================

Return:

1. Branch
2. Commit hash
3. Classification document
4. Validator changes
5. Readiness gate changes
6. Test result
7. Safety report
8. Git tag

FINAL STATUS:

WAITING_FOR_ARCHITECT_REVIEW

STOP.

DO NOT EXECUTE SHUTDOWN.
DO NOT START PHASE 11.2.
