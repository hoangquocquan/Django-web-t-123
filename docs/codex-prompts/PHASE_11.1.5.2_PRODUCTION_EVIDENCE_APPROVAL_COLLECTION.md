# TASK: Phase 11.1.5.2 - Production Evidence & Approval Collection


Project:

mecprecision-vietnam



====================================================
SAVE THIS PROMPT
====================================================


Before implementation:


Save this task specification into:


C:\Users\hoang\Documents\Codex\mecprecision-vietnam\docs\codex-prompts


Filename:


PHASE_11.1.5.2_PRODUCTION_EVIDENCE_APPROVAL_COLLECTION.md



====================================================
STATUS
====================================================


Completed:


Phase 11.1.5.1
Production Evidence & Approval Completion



Current decision:


KEEP_LEGACY_API_ACTIVE



Missing:


- Production traffic evidence
- Production log validation
- Technical approval
- Business approval
- Rollback ownership
- Maintenance window
- Monitoring confirmation



====================================================
OBJECTIVE
====================================================


Collect real production evidence and approval inputs
required before Legacy API shutdown.



Target:


Change from:


KEEP_LEGACY_API_ACTIVE


to:


READY_FOR_LEGACY_API_SHUTDOWN



ONLY when all requirements are verified.



====================================================
IMPORTANT RULES
====================================================


DO NOT:


- disable legacy API
- modify proxy
- change routes
- archive database
- delete legacy code



ONLY:


- collect evidence
- validate documents
- prepare approval package



====================================================
READ REQUIRED DOCUMENTS
====================================================


Read:


docs/migration/PRODUCTION_EVIDENCE_COMPLETION_CHECKLIST.md


docs/migration/LEGACY_API_FINAL_APPROVAL_RECORD.md


docs/migration/LEGACY_API_FINAL_SHUTDOWN_DECISION.md


docs/migration/PRODUCTION_TRAFFIC_EVIDENCE_REPORT.md


docs/migration/LEGACY_API_DECOMMISSION_ROLLBACK.md



====================================================
TASK 1
====================================================


Create Production Evidence Input Template.



Create:


docs/migration/PRODUCTION_EVIDENCE_INPUT_TEMPLATE.md



Include:



Traffic period:


Start date:

End date:



Log sources:


[ ] Nginx

[ ] Load balancer

[ ] API gateway

[ ] Application logs

[ ] CDN



Metrics:


Legacy API requests:

/api/


Django API requests:

/api/v1/


Unknown clients:



Evidence owner:



Evidence timestamp:



====================================================
TASK 2
====================================================


Create Client Confirmation Template.



Create:


docs/migration/LEGACY_API_CLIENT_CONFIRMATION_RECORD.md



Include:


Client:

Owner:

Legacy API usage:

Replacement API:

Migration completed:

Confirmation date:



Sources:


Frontend

Mobile

Integration

Partner

Internal scripts



====================================================
TASK 3
====================================================


Create Approval Collection Template.



Create:


docs/migration/LEGACY_API_SHUTDOWN_APPROVAL_COLLECTION.md



Include:


Technical approval:


Name:

Role:

Date:

Signature:



Business approval:


Name:

Role:

Date:

Signature:



Rollback owner:


Name:

Contact:



Maintenance window:


Start:

End:



Monitoring owner:



====================================================
TASK 4
====================================================


Create Evidence Validation Checklist.



Create:


docs/migration/FINAL_SHUTDOWN_EVIDENCE_CHECKLIST.md



Validate:


Traffic:


[ ] Legacy API traffic = 0

[ ] Django API active


Dependencies:


[ ] No unknown clients


Operations:


[ ] Rollback ready

[ ] Monitoring ready


Approvals:


[ ] Technical approved

[ ] Business approved



====================================================
TASK 5
====================================================


Update Shutdown Decision Template.



Update:


docs/migration/LEGACY_API_FINAL_SHUTDOWN_DECISION.md



Add:


Evidence references

Approval references

Owner information

Final decision



Allowed:


READY_FOR_LEGACY_API_SHUTDOWN


KEEP_LEGACY_API_ACTIVE



====================================================
TASK 6
====================================================


Create Validation Script.



Create:


scripts/phase11_1_5_2_evidence_approval_validator.py



Validate:


Evidence:


legacy_requests == 0


unknown_clients == 0



Approval:


technical=true

business=true



Operations:


rollback=true

monitoring=true



Output:


READY_FOR_LEGACY_API_SHUTDOWN


or


KEEP_LEGACY_API_ACTIVE



====================================================
TASK 7
====================================================


Create Tests.



Create:


django_backend/tests/test_phase11_1_5_2_evidence_approval.py



Test:


- missing evidence blocked

- missing approval blocked

- incomplete client confirmation blocked

- complete package accepted



====================================================
TASK 8
====================================================


Testing.



Run:


python scripts/phase11_1_5_2_evidence_approval_validator.py


python manage.py check


pytest django_backend\tests\test_phase11_1_5_2_evidence_approval.py


pytest


powershell -ExecutionPolicy Bypass -File scripts\run_migration_test.ps1



Expected:


Without real evidence:


KEEP_LEGACY_API_ACTIVE



With complete evidence:


READY_FOR_LEGACY_API_SHUTDOWN



====================================================
TASK 9
====================================================


Create Review Package.



Create:


docs/reviews/


PHASE_11.1.5.2_REVIEW_SUMMARY.md


PHASE_11.1.5.2_CHANGESET.patch



Include:


Evidence status

Approval status

Validation result

Testing result

Recommendation



====================================================
GIT REQUIREMENTS
====================================================


Create branch:


migration/phase-11.1.5.2-evidence-approval-collection



Commit:


git add .


git commit -m "feat: add production evidence approval collection"



Create tag:


phase-11.1.5.2-evidence-ready



====================================================
FINAL OUTPUT
====================================================


Return:


1. Branch

2. Commit

3. Evidence status

4. Approval status

5. Readiness decision

6. Testing result

7. Review package

8. Git tag



FINAL STATUS:


WAITING FOR ARCHITECT REVIEW


STOP.

DO NOT START PHASE 11.1.6 OR PHASE 11.2.