# TASK: Phase 11.1.5.1 - Production Evidence & Approval Completion


Project:

mecprecision-vietnam



====================================================
SAVE THIS PROMPT
====================================================


Before implementation:


Save this task specification into:


C:\Users\hoang\Documents\Codex\mecprecision-vietnam\docs\codex-prompts


Filename:


PHASE_11.1.5.1_PRODUCTION_EVIDENCE_APPROVAL_COMPLETION.md



====================================================
STATUS
====================================================


Completed:


Phase 11.1.1
Django API Replacement Completion


Phase 11.1.2
Legacy API Traffic Verification


Phase 11.1.3
Legacy API Decommission Execution Gate


Phase 11.1.4
Production Traffic Evidence Collection


Phase 11.1.5
Legacy API Shutdown Readiness Approval



Current decision:


KEEP_LEGACY_API_ACTIVE



Current blockers:


- Production traffic evidence missing

- Legacy traffic zero not verified

- Django API active usage not verified

- Technical approval missing

- Business approval missing

- Rollback owner missing

- Maintenance window missing



====================================================
OBJECTIVE
====================================================


Complete all missing evidence and approvals required
before Legacy API shutdown.



Goal:


Change status from:


KEEP_LEGACY_API_ACTIVE


to:


READY_FOR_LEGACY_API_SHUTDOWN



ONLY when all requirements are satisfied.



====================================================
IMPORTANT RULES
====================================================


DO NOT:


- disable legacy API

- change routing

- modify proxy

- archive database

- remove legacy code



ONLY:


- collect evidence

- validate readiness

- prepare approval records



====================================================
READ REQUIRED DOCUMENTS
====================================================


Read:


docs/migration/PRODUCTION_TRAFFIC_EVIDENCE_REPORT.md


docs/migration/LEGACY_API_SHUTDOWN_APPROVAL_PACKAGE.md


docs/migration/LEGACY_API_FINAL_SHUTDOWN_DECISION.md


docs/migration/LEGACY_API_SHUTDOWN_APPROVAL_RECORD.md


docs/migration/LEGACY_API_DECOMMISSION_ROLLBACK.md



====================================================
TASK 1
====================================================


Create Evidence Completion Checklist.



Create:


docs/migration/PRODUCTION_EVIDENCE_COMPLETION_CHECKLIST.md



Include:


Traffic evidence:


[ ] Nginx logs collected

[ ] Load balancer logs collected

[ ] API gateway checked

[ ] Application logs checked

[ ] CDN checked if applicable


Traffic validation:


[ ] Legacy /api traffic = 0

[ ] Django /api/v1 traffic confirmed

[ ] Unknown clients = 0



====================================================
TASK 2
====================================================


Create Approval Completion Record.



Create:


docs/migration/LEGACY_API_FINAL_APPROVAL_RECORD.md



Include:


Technical approval:

Name

Role

Date


Business approval:

Name

Role

Date


Rollback owner:

Name

Contact


Maintenance window:


Start

End



====================================================
TASK 3
====================================================


Update Shutdown Decision.



Update:


docs/migration/LEGACY_API_FINAL_SHUTDOWN_DECISION.md



Add:


Evidence status

Approval status

Risk status

Final decision



Allowed:


READY_FOR_LEGACY_API_SHUTDOWN


or


KEEP_LEGACY_API_ACTIVE



====================================================
TASK 4
====================================================


Create Final Readiness Validator.



Create:


scripts/phase11_1_5_1_final_shutdown_readiness.py



Validate:


Traffic:


legacy_requests == 0


unknown_clients == 0



Approval:


technical_approval == true

business_approval == true


Operations:


rollback_ready == true

monitoring_ready == true



Output:


READY_FOR_LEGACY_API_SHUTDOWN


or


KEEP_LEGACY_API_ACTIVE



====================================================
TASK 5
====================================================


Create Tests.



Create:


django_backend/tests/test_phase11_1_5_1_final_shutdown_readiness.py



Test:


- missing logs blocked

- missing approval blocked

- unknown clients blocked

- rollback missing blocked

- complete approval passed



====================================================
TASK 6
====================================================


Testing.



Run:


python scripts/phase11_1_5_1_final_shutdown_readiness.py


python manage.py check


pytest django_backend\tests\test_phase11_1_5_1_final_shutdown_readiness.py


pytest


powershell -ExecutionPolicy Bypass -File scripts\run_migration_test.ps1



Expected:


Without real production evidence:


KEEP_LEGACY_API_ACTIVE



With complete evidence:


READY_FOR_LEGACY_API_SHUTDOWN



====================================================
TASK 7
====================================================


Create Review Package.



Create:


docs/reviews/


PHASE_11.1.5.1_REVIEW_SUMMARY.md


PHASE_11.1.5.1_CHANGESET.patch



Include:


Objective

Evidence completion

Approval completion

Risk assessment

Testing result

Recommendation



====================================================
GIT REQUIREMENTS
====================================================


Create branch:


migration/phase-11.1.5.1-production-approval-completion



Commit:


git add .


git commit -m "feat: complete legacy api shutdown approval readiness"



Create tag:


phase-11.1.5.1-approval-complete



====================================================
FINAL OUTPUT
====================================================


Return:


1.

Branch name


2.

Commit hash


3.

Evidence status


4.

Approval status


5.

Final readiness decision


6.

Testing result


7.

Review package location


8.

Git tag



FINAL STATUS:


WAITING FOR ARCHITECT REVIEW


STOP.

DO NOT START PHASE 11.1.6 OR PHASE 11.2.