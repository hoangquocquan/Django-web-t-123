# TASK: Phase 11.1.2 - Legacy API Traffic Verification


Project:

mecprecision-vietnam



====================================================
SAVE THIS PROMPT
====================================================


Before implementation:


Save this task specification into:


C:\Users\hoang\Documents\Codex\mecprecision-vietnam\docs\codex-prompts


Filename:


PHASE_11.1.2_LEGACY_API_TRAFFIC_VERIFICATION.md



====================================================
STATUS
====================================================


Completed:


Phase 11.1
Legacy API Decommission Governance


Phase 11.1.1
Django API Replacement Completion



Current status:


15/15 legacy API route groups have Django replacements.



Current blocker:


No production traffic evidence proving legacy API usage is zero.



====================================================
OBJECTIVE
====================================================


Verify that no active clients depend on legacy API routes
before disabling legacy API endpoints.



Goal:


Confirm:


Legacy:

/api/...


Traffic:


ZERO


Replacement:


/api/v1/...


Active usage confirmed



====================================================
IMPORTANT RULES
====================================================


DO NOT:


- disable legacy API routes
- modify production proxy
- remove legacy API code
- remove compatibility adapters
- delete logs


ONLY:


- analyze traffic
- create verification tools
- document evidence
- prepare decommission decision



====================================================
READ REQUIRED DOCUMENTS
====================================================


Read:


docs/migration/LEGACY_API_COMPATIBILITY_MATRIX.md


docs/migration/LEGACY_API_DECOMMISSION_AUDIT.md


docs/migration/LEGACY_API_DECOMMISSION_RUNBOOK.md


docs/api/LEGACY_API_REPLACEMENT_STATUS.md


docs/migration/PRODUCTION_CUTOVER_REPORT.md


docs/testing/PHASE_TESTING_STANDARD.md



====================================================
TASK 1
====================================================


Create Legacy API Traffic Audit Document.



Create:


docs/migration/LEGACY_API_TRAFFIC_AUDIT.md



Include:


Traffic sources:


- frontend applications

- mobile clients

- integrations

- scheduled jobs

- internal scripts


For each:


Source

Legacy API usage

Replacement API

Status



====================================================
TASK 2
====================================================


Create Traffic Verification Script.



Create:


scripts/phase11_1_2_legacy_api_traffic_verification.py



Requirements:


Analyze:


- API access logs

- proxy logs

- application logs

- integration logs


Detect:


Legacy routes:


/api/...


Exclude:


/api/v1/...



Output:


JSON report:



Example:


{
 "legacy_requests":0,
 "replacement_requests":100,
 "safe_to_decommission":true
}



====================================================
TASK 3
====================================================


Create API Usage Report.



Create:


docs/migration/LEGACY_API_TRAFFIC_VERIFICATION_REPORT.md



Include:


Verification period

Traffic sources checked

Legacy API calls

Replacement API calls

Unknown clients

Decision



Possible results:


READY_FOR_DECOMMISSION


or


KEEP_LEGACY_API_ACTIVE



====================================================
TASK 4
====================================================


Create Client Dependency Scanner.



Create:


scripts/phase11_1_2_api_dependency_scanner.py



Scan:


- frontend source

- JavaScript files

- configuration files

- integration configs

- scheduled scripts



Detect:


References:


/api/


Legacy endpoint names



Report:


File

Reference

Replacement status



====================================================
TASK 5
====================================================


Create Safety Tests.



Create:


django_backend/tests/test_phase11_1_2_legacy_api_traffic.py



Test:


- legacy route detection

- api/v1 exclusion

- unknown client detection

- empty traffic report handling

- safe decommission decision



====================================================
TASK 6
====================================================


Security Review.



Verify:


- logs do not expose secrets

- tokens are masked

- credentials removed

- customer data protected



====================================================
TASK 7
====================================================


Testing.



Run:


python scripts/phase11_1_2_legacy_api_traffic_verification.py


python scripts/phase11_1_2_api_dependency_scanner.py


python manage.py check


pytest django_backend\tests\test_phase11_1_2_legacy_api_traffic.py


pytest


powershell -ExecutionPolicy Bypass -File scripts\run_migration_test.ps1



Expected:


All verification tests PASS.



====================================================
TASK 8
====================================================


Create Review Package.



Create:


docs/reviews/


PHASE_11.1.2_REVIEW_SUMMARY.md


PHASE_11.1.2_CHANGESET.patch



Summary:


Objective

Traffic verification result

Legacy API usage

Dependency scan

Security review

Testing result

Recommendation



====================================================
GIT REQUIREMENTS
====================================================


Create branch:


migration/phase-11.1.2-legacy-api-traffic-verification



Commit:


git add .


git commit -m "feat: add legacy api traffic verification"



Create tag:


phase-11.1.2-traffic-verified



====================================================
FINAL OUTPUT
====================================================


Return:


1.

Branch name


2.

Base commit


3.

Final commit


4.

Legacy API traffic result


5.

Dependency scan result


6.

Testing result


7.

Review package location


8.

Git tag



FINAL STATUS:


WAITING FOR ARCHITECT REVIEW


STOP.

DO NOT START PHASE 11.1.3 OR PHASE 11.2.