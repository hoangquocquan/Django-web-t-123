# TASK: Phase 11.1.5.4 - Real Production Data Collection & Validation


Project:

mecprecision-vietnam



====================================================
SAVE THIS PROMPT
====================================================


Save this task specification into:


C:\Users\hoang\Documents\Codex\mecprecision-vietnam\docs\codex-prompts


Filename:


PHASE_11.1.5.4_REAL_PRODUCTION_DATA_COLLECTION_VALIDATION.md



====================================================
CURRENT STATUS
====================================================


Completed:


Phase 11.1.1
Django API Replacement


Phase 11.1.2
Legacy API Traffic Verification


Phase 11.1.3
Legacy API Decommission Gate


Phase 11.1.4
Production Traffic Evidence Framework


Phase 11.1.5
Shutdown Readiness Approval


Phase 11.1.5.1
Evidence Completion Framework


Phase 11.1.5.2
Evidence Approval Collection


Phase 11.1.5.3
Production Evidence Package Structure



Current validation:


INCOMPLETE_EVIDENCE_PACKAGE



Reason:


Production data has not been collected.



====================================================
OBJECTIVE
====================================================


Collect and validate REAL production evidence before
Legacy API shutdown.



Goal:


Change:


INCOMPLETE_EVIDENCE_PACKAGE


to:


COMPLETE_EVIDENCE_PACKAGE



====================================================
IMPORTANT RULES
====================================================


DO NOT:


- shutdown Legacy API

- modify routing

- remove legacy code

- archive database



ONLY:


- collect production evidence

- validate traffic

- validate dependencies

- validate approvals



====================================================
READ REQUIRED DOCUMENTS
====================================================


Read:


docs/migration/production_evidence/


docs/migration/FINAL_SHUTDOWN_EVIDENCE_CHECKLIST.md


docs/migration/LEGACY_API_FINAL_SHUTDOWN_DECISION.md


docs/migration/LEGACY_API_DECOMMISSION_ROLLBACK.md



====================================================
TASK 1
====================================================


Create Production Data Import Guide.



Create:


docs/migration/production_evidence/REAL_PRODUCTION_DATA_IMPORT_GUIDE.md



Include:


Supported sources:


- Nginx logs

- Load balancer logs

- API gateway logs

- Application logs

- CSV export

- JSON export



Required fields:


timestamp

client

endpoint

status_code

request_count



====================================================
TASK 2
====================================================


Create Production Evidence Loader.



Create:


scripts/phase11_1_5_4_production_evidence_loader.py



Input:


CSV

JSON

Log files



Process:


Detect:


Legacy:


/api/*



Django:


/api/v1/*



Calculate:


legacy_requests

django_requests

unknown_clients

error_rate



Output:


docs/migration/production_evidence/reports/REAL_PRODUCTION_TRAFFIC_REPORT.json



Example:


{
 "legacy_requests":0,
 "django_requests":10000,
 "unknown_clients":0,
 "ready_for_shutdown":true
}



====================================================
TASK 3
====================================================


Update Evidence Reports.



Update:


docs/migration/production_evidence/reports/EVIDENCE_PACKAGE_STATUS.md



Include:


Data source

Collection period

Validation result

Owner

Timestamp



====================================================
TASK 4
====================================================


Create Client Dependency Validation.



Create:


scripts/phase11_1_5_4_client_dependency_validator.py



Validate:


No unknown clients

All clients migrated

No legacy dependency



Output:


CLIENTS_READY


or


CLIENT_MIGRATION_REQUIRED



====================================================
TASK 5
====================================================


Create Final Production Evidence Report.



Create:


docs/migration/production_evidence/reports/FINAL_PRODUCTION_EVIDENCE_REPORT.md



Include:


Verification period

Traffic result

Client result

API comparison

Risk assessment

Recommendation



Possible:


READY_FOR_LEGACY_API_SHUTDOWN


KEEP_LEGACY_API_ACTIVE



====================================================
TASK 6
====================================================


Create Tests.



Create:


django_backend/tests/test_phase11_1_5_4_production_evidence.py



Test:


- empty data blocked

- legacy traffic detected

- zero legacy traffic accepted

- unknown client detected

- valid production package accepted



====================================================
TASK 7
====================================================


Testing.



Run:


python scripts\phase11_1_5_4_production_evidence_loader.py


python scripts\phase11_1_5_4_client_dependency_validator.py


python manage.py check


pytest django_backend\tests\test_phase11_1_5_4_production_evidence.py


pytest


powershell -ExecutionPolicy Bypass -File scripts\run_migration_test.ps1



Expected:


Without real data:


INCOMPLETE_EVIDENCE_PACKAGE



With valid production data:


COMPLETE_EVIDENCE_PACKAGE



====================================================
TASK 8
====================================================


Create Review Package.



Create:


docs/reviews/


PHASE_11.1.5.4_REVIEW_SUMMARY.md


PHASE_11.1.5.4_CHANGESET.patch



Include:


Production data sources

Traffic analysis

Client validation

Risk assessment

Testing

Recommendation



====================================================
GIT REQUIREMENTS
====================================================


Create branch:


migration/phase-11.1.5.4-real-production-evidence



Commit:


git add .


git commit -m "feat: add real production evidence validation"



Create tag:


phase-11.1.5.4-production-evidence-complete



====================================================
FINAL OUTPUT
====================================================


Return:


1. Branch

2. Commit hash

3. Production data sources

4. Legacy API request count

5. Django API request count

6. Unknown clients

7. Validation result

8. Testing result

9. Review package


FINAL STATUS:


WAITING_FOR_ARCHITECT_REVIEW


STOP.

DO NOT START PHASE 11.1.6 OR PHASE 11.2.