# TASK: Phase 11.1.5 - Legacy API Shutdown Readiness Approval


Project:

mecprecision-vietnam



====================================================
SAVE THIS PROMPT
====================================================


Before implementation:


Save this task specification into:


C:\Users\hoang\Documents\Codex\mecprecision-vietnam\docs\codex-prompts


Filename:


PHASE_11.1.5_LEGACY_API_SHUTDOWN_READINESS_APPROVAL.md



====================================================
STATUS
====================================================


Completed:


Phase 11.0
Legacy Shutdown Governance


Phase 11.1.1
Django API Replacement Completion


Phase 11.1.2
Legacy API Traffic Verification


Phase 11.1.3
Legacy API Decommission Execution Gate


Phase 11.1.4
Production Traffic Evidence Collection



Current situation:


Technical preparation completed.

Final shutdown approval package is missing.



====================================================
OBJECTIVE
====================================================


Create final readiness approval process before
executing Legacy API shutdown.



Goal:


Determine:


READY_FOR_LEGACY_API_SHUTDOWN


or


KEEP_LEGACY_API_ACTIVE



====================================================
IMPORTANT RULES
====================================================


DO NOT:


- disable API routes
- modify production routing
- delete legacy code
- archive database
- remove rollback capability



ONLY:


- validate readiness
- collect approvals
- create decision package



====================================================
READ REQUIRED DOCUMENTS
====================================================


Read:


docs/migration/PRODUCTION_TRAFFIC_EVIDENCE_REPORT.md


docs/migration/LEGACY_API_SHUTDOWN_APPROVAL_PACKAGE.md


docs/migration/LEGACY_API_DECOMMISSION_EXECUTION_PLAN.md


docs/migration/LEGACY_API_DECOMMISSION_ROLLBACK.md


docs/migration/LEGACY_API_COMPATIBILITY_MATRIX.md



====================================================
TASK 1
====================================================


Create Shutdown Readiness Checklist.



Create:


docs/migration/LEGACY_API_SHUTDOWN_READINESS_CHECKLIST.md



Include:



Technical:


[ ] Django APIs available

[ ] API compatibility completed

[ ] Legacy traffic verified

[ ] Monitoring ready


Operational:


[ ] Maintenance window approved

[ ] Rollback owner assigned

[ ] Support team notified


Business:


[ ] Business owner approval

[ ] User impact reviewed



====================================================
TASK 2
====================================================


Create Approval Validation Script.



Create:


scripts/phase11_1_5_shutdown_readiness_check.py



Validate:



API:


replacement_ready=true


Traffic:


legacy_requests=0


Security:


no unknown clients


Operations:


rollback_ready=true


Approval:


business_approved=true

technical_approved=true



Output:



READY_FOR_LEGACY_API_SHUTDOWN


or


KEEP_LEGACY_API_ACTIVE



====================================================
TASK 3
====================================================


Create Final Decision Report.



Create:


docs/migration/LEGACY_API_FINAL_SHUTDOWN_DECISION.md



Include:



Current state

Evidence summary

Risk assessment

Rollback plan

Approval status

Final decision



====================================================
TASK 4
====================================================


Create Production Shutdown Runbook Update.



Update:


docs/migration/LEGACY_API_DECOMMISSION_EXECUTION_PLAN.md



Add:


Owner

Timeline

Validation steps

Rollback steps

Post shutdown monitoring



====================================================
TASK 5
====================================================


Create Approval Audit Record.



Create:


docs/migration/LEGACY_API_SHUTDOWN_APPROVAL_RECORD.md



Include:


Technical approval

Business approval

Date

Decision

Evidence references



====================================================
TASK 6
====================================================


Create Tests.



Create:


django_backend/tests/test_phase11_1_5_shutdown_readiness.py



Test:


- missing evidence blocked

- missing approval blocked

- unknown client blocked

- rollback missing blocked

- full approval accepted



====================================================
TASK 7
====================================================


Testing.



Run:


python scripts/phase11_1_5_shutdown_readiness_check.py


python manage.py check


pytest django_backend\tests\test_phase11_1_5_shutdown_readiness.py


pytest


powershell -ExecutionPolicy Bypass -File scripts\run_migration_test.ps1



Expected:


Without production approval:


KEEP_LEGACY_API_ACTIVE



With complete evidence:


READY_FOR_LEGACY_API_SHUTDOWN



====================================================
TASK 8
====================================================


Create Review Package.



Create:


docs/reviews/


PHASE_11.1.5_REVIEW_SUMMARY.md


PHASE_11.1.5_CHANGESET.patch



Include:


Objective

Readiness result

Evidence status

Approval status

Risk assessment

Testing result

Recommendation



====================================================
GIT REQUIREMENTS
====================================================


Create branch:


migration/phase-11.1.5-api-shutdown-readiness



Commit:


git add .


git commit -m "feat: add legacy api shutdown readiness approval"



Create tag:


phase-11.1.5-shutdown-readiness



====================================================
FINAL OUTPUT
====================================================


Return:


1.

Branch name


2.

Commit hash


3.

Readiness result


4.

Evidence status


5.

Approval status


6.

Testing result


7.

Review package location


8.

Git tag



FINAL STATUS:


WAITING FOR ARCHITECT REVIEW


STOP.

DO NOT START PHASE 11.2.