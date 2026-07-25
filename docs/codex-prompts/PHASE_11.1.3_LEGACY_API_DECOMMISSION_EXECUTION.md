# TASK: Phase 11.1.3 - Legacy API Decommission Execution


Project:

mecprecision-vietnam



====================================================
SAVE THIS PROMPT
====================================================


Before implementation:


Save this task specification into:


C:\Users\hoang\Documents\Codex\mecprecision-vietnam\docs\codex-prompts


Filename:


PHASE_11.1.3_LEGACY_API_DECOMMISSION_EXECUTION.md



====================================================
STATUS
====================================================


Completed:


Phase 11.0
Legacy Shutdown Governance


Phase 11.1
Legacy API Decommission Governance


Phase 11.1.1
Django API Replacement Completion


Phase 11.1.2
Legacy API Traffic Verification



Current status:


Legacy API replacements completed.

Traffic verification tooling completed.



IMPORTANT:


Production traffic evidence is required before execution.



====================================================
OBJECTIVE
====================================================


Safely disable legacy API routes after confirming
all clients have migrated to Django API endpoints.



Goal:


Legacy:


/api/...


        ↓


DISABLED


Django:


/api/v1/...


        ↓


ACTIVE



====================================================
SAFETY RULES
====================================================


DO NOT EXECUTE DECOMMISSION IF:


- production traffic evidence missing

- unknown clients exist

- approval missing

- rollback plan missing



If requirements are missing:


Return:


BLOCKED_SAFELY



Do NOT:


- delete legacy API code
- delete database
- remove compatibility layer
- remove logs
- change unrelated routes



====================================================
READ REQUIRED DOCUMENTS
====================================================


Read:


docs/migration/LEGACY_API_TRAFFIC_VERIFICATION_REPORT.md


docs/migration/LEGACY_API_COMPATIBILITY_MATRIX.md


docs/migration/LEGACY_API_DECOMMISSION_RUNBOOK.md


docs/migration/PRODUCTION_ROLLBACK_EXECUTION_GUIDE.md


docs/testing/PHASE_TESTING_STANDARD.md



====================================================
TASK 1
====================================================


Create API Decommission Approval Gate.



Create:


scripts/phase11_1_3_api_decommission_gate.py



Validate:


Required:


- traffic verification status

- approval ID

- operator confirmation

- rollback owner

- rollback plan


Reject:


- missing approval

- unknown clients

- non-zero legacy traffic



====================================================
TASK 2
====================================================


Create Legacy API Disable Workflow.



Create:


docs/migration/LEGACY_API_DECOMMISSION_EXECUTION_PLAN.md



Include:


Before:


[ ] Traffic verified zero

[ ] Backup confirmed

[ ] Rollback ready

[ ] Approval completed



Execution:


[ ] Disable legacy routes

[ ] Enable monitoring

[ ] Verify Django APIs



After:


[ ] Monitor errors

[ ] Confirm no legacy calls

[ ] Record decision



====================================================
TASK 3
====================================================


Create Controlled Disable Script.



Create:


scripts/phase11_1_3_disable_legacy_api.py



Requirements:


Default:


SAFE BLOCK MODE



Only allow execution when:


PHASE11_APPROVAL=approved


PHASE11_TRAFFIC_ZERO=true


PHASE11_ROLLBACK_READY=true



Actions:


Disable:


/api/...


ONLY



Do NOT modify:


/api/v1/...



====================================================
TASK 4
====================================================


Create Rollback Procedure.



Create:


docs/migration/LEGACY_API_DECOMMISSION_ROLLBACK.md



Include:


Rollback triggers:


- API errors

- client failures

- business interruption


Rollback steps:


- restore routes

- restore proxy rules

- validate API health



====================================================
TASK 5
====================================================


Create Monitoring Checklist.



Create:


docs/monitoring/LEGACY_API_DECOMMISSION_MONITORING.md



Monitor:


- HTTP errors

- API latency

- Django errors

- customer reports

- integration failures



====================================================
TASK 6
====================================================


Create Tests.



Create:


django_backend/tests/test_phase11_1_3_api_decommission.py



Test:


- missing approval blocked

- traffic not zero blocked

- rollback missing blocked

- approved execution allowed

- Django API unaffected



====================================================
TASK 7
====================================================


Testing.



Run:


python scripts/phase11_1_3_api_decommission_gate.py


python scripts/phase11_1_3_disable_legacy_api.py


python manage.py check


pytest django_backend\tests\test_phase11_1_3_api_decommission.py


pytest


powershell -ExecutionPolicy Bypass -File scripts\run_migration_test.ps1



Expected:


Default environment:


BLOCKED_SAFELY



====================================================
TASK 8
====================================================


Create Review Package.



Create:


docs/reviews/


PHASE_11.1.3_REVIEW_SUMMARY.md


PHASE_11.1.3_CHANGESET.patch



Include:


Objective

Approval gate

Execution status

Rollback readiness

Monitoring

Testing

Recommendation



====================================================
GIT REQUIREMENTS
====================================================


Create branch:


migration/phase-11.1.3-legacy-api-decommission



Commit:


git add .


git commit -m "feat: add controlled legacy api decommission workflow"



Create tag:


phase-11.1.3-api-decommission-ready



====================================================
FINAL OUTPUT
====================================================


Return:


1.

Branch name


2.

Commit hash


3.

Execution status


4.

Safety gate result


5.

Testing result


6.

Review package location


7.

Git tag



FINAL STATUS:


WAITING FOR ARCHITECT REVIEW


STOP.

DO NOT START PHASE 11.2.