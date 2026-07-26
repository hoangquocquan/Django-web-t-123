# TASK: Phase 11.1.5.3 - Production Evidence Data Collection


Project:

mecprecision-vietnam



====================================================
SAVE THIS PROMPT
====================================================


Before implementation:


Save this task specification into:


C:\Users\hoang\Documents\Codex\mecprecision-vietnam\docs\codex-prompts


Filename:


PHASE_11.1.5.3_PRODUCTION_EVIDENCE_DATA_COLLECTION.md



====================================================
STATUS
====================================================


Completed:


Phase 11.1.5.2
Production Evidence & Approval Collection



Current decision:


KEEP_LEGACY_API_ACTIVE



Existing framework:


- Evidence templates created

- Approval templates created

- Validation scripts created



Missing real inputs:


- Production logs

- Client confirmations

- Technical approval

- Business approval

- Rollback owner

- Maintenance window



====================================================
OBJECTIVE
====================================================


Create operational data collection package
for final Legacy API shutdown approval.



Goal:


Prepare complete evidence package:


Production traffic proof

+

Client migration confirmation

+

Operational approval



====================================================
IMPORTANT RULES
====================================================


DO NOT:


- disable legacy API

- change routes

- modify proxy

- archive database

- remove legacy code



ONLY:


- create collection documents

- create input structure

- validate completeness



====================================================
READ REQUIRED DOCUMENTS
====================================================


Read:


docs/migration/PRODUCTION_EVIDENCE_INPUT_TEMPLATE.md


docs/migration/LEGACY_API_CLIENT_CONFIRMATION_RECORD.md


docs/migration/LEGACY_API_SHUTDOWN_APPROVAL_COLLECTION.md


docs/migration/FINAL_SHUTDOWN_EVIDENCE_CHECKLIST.md


docs/migration/LEGACY_API_FINAL_SHUTDOWN_DECISION.md



====================================================
TASK 1
====================================================


Create Production Evidence Package Folder.



Create:


docs/migration/production_evidence/



Structure:


production_evidence/


├── traffic/

├── clients/

├── approvals/

├── monitoring/

└── reports/



====================================================
TASK 2
====================================================


Create Traffic Evidence Input Files.



Create:


docs/migration/production_evidence/traffic/


LEGACY_API_TRAFFIC_LOG_SUMMARY.md


LEGACY_API_TRAFFIC_EXPORT_TEMPLATE.csv



Include:


Verification period

Log source

Total requests

Legacy API requests:

/api/


Django API requests:

/api/v1/


Unknown clients



====================================================
TASK 3
====================================================


Create Client Confirmation Package.



Create:


docs/migration/production_evidence/clients/


CLIENT_MIGRATION_CONFIRMATION_TEMPLATE.md


CLIENT_DEPENDENCY_MATRIX.csv



Include:


Client

Owner

Legacy API usage

Replacement API

Migration date

Confirmation



====================================================
TASK 4
====================================================


Create Approval Package.



Create:


docs/migration/production_evidence/approvals/


TECHNICAL_APPROVAL.md


BUSINESS_APPROVAL.md


ROLLBACK_OWNER.md


MAINTENANCE_WINDOW.md



Include:


Name

Role

Date

Confirmation



====================================================
TASK 5
====================================================


Create Monitoring Confirmation.



Create:


docs/migration/production_evidence/monitoring/


MONITORING_READINESS_CONFIRMATION.md



Include:


Error monitoring

API monitoring

Alert owner

Rollback trigger

Support contact



====================================================
TASK 6
====================================================


Create Evidence Completeness Validator.



Create:


scripts/phase11_1_5_3_evidence_package_validator.py



Validate:


Required files exist:


traffic evidence

client confirmations

technical approval

business approval

rollback owner

maintenance window

monitoring confirmation



Output:


INCOMPLETE_EVIDENCE_PACKAGE


or


COMPLETE_EVIDENCE_PACKAGE



====================================================
TASK 7
====================================================


Create Tests.



Create:


django_backend/tests/test_phase11_1_5_3_evidence_package.py



Test:


- missing evidence blocked

- missing approval blocked

- missing client confirmation blocked

- complete package accepted



====================================================
TASK 8
====================================================


Testing.



Run:


python scripts/phase11_1_5_3_evidence_package_validator.py


python manage.py check


pytest django_backend\tests\test_phase11_1_5_3_evidence_package.py


pytest


powershell -ExecutionPolicy Bypass -File scripts\run_migration_test.ps1



Expected:


Without real evidence:


INCOMPLETE_EVIDENCE_PACKAGE



With complete evidence:


COMPLETE_EVIDENCE_PACKAGE



====================================================
TASK 9
====================================================


Create Review Package.



Create:


docs/reviews/


PHASE_11.1.5.3_REVIEW_SUMMARY.md


PHASE_11.1.5.3_CHANGESET.patch



Include:


Package structure

Validation result

Missing items

Testing result

Recommendation



====================================================
GIT REQUIREMENTS
====================================================


Create branch:


migration/phase-11.1.5.3-production-evidence-package



Commit:


git add .


git commit -m "feat: create production evidence collection package"



Create tag:


phase-11.1.5.3-evidence-package-ready



====================================================
FINAL OUTPUT
====================================================


Return:


1. Branch

2. Commit

3. Evidence package status

4. Missing requirements

5. Testing result

6. Review package

7. Git tag



FINAL STATUS:


WAITING_FOR_ARCHITECT_REVIEW


STOP.

DO NOT START PHASE 11.1.6 OR PHASE 11.2.