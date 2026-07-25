# TASK: Phase 11.1.4 - Production Traffic Evidence Collection


Project:

mecprecision-vietnam



====================================================
SAVE THIS PROMPT
====================================================


Before implementation:


Save this task specification into:


C:\Users\hoang\Documents\Codex\mecprecision-vietnam\docs\codex-prompts


Filename:


PHASE_11.1.4_PRODUCTION_TRAFFIC_EVIDENCE_COLLECTION.md



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
Legacy API Traffic Verification Tooling


Phase 11.1.3
Legacy API Decommission Execution Gate



Current blocker:


Production traffic evidence is missing.



Current state:


Legacy API remains active.



====================================================
OBJECTIVE
====================================================


Collect production evidence proving whether legacy
API routes still receive traffic before decommission.



Goal:


Verify:


Legacy API:


/api/...


Traffic:


ZERO



Django API:


/api/v1/...


Active usage confirmed



====================================================
IMPORTANT RULES
====================================================


DO NOT:


- disable legacy API
- change proxy rules
- remove routes
- remove logs
- delete legacy system


ONLY:


- collect evidence
- analyze logs
- document results
- prepare approval package



====================================================
READ REQUIRED DOCUMENTS
====================================================


Read:


docs/migration/LEGACY_API_TRAFFIC_VERIFICATION_REPORT.md


docs/migration/LEGACY_API_DECOMMISSION_EXECUTION_PLAN.md


docs/migration/LEGACY_API_DECOMMISSION_ROLLBACK.md


docs/migration/LEGACY_API_COMPATIBILITY_MATRIX.md


docs/testing/PHASE_TESTING_STANDARD.md



====================================================
TASK 1
====================================================


Create Production Traffic Evidence Checklist.



Create:


docs/migration/PRODUCTION_TRAFFIC_EVIDENCE_CHECKLIST.md



Include:


Required evidence:


[ ] Nginx access logs

[ ] Load balancer logs

[ ] API gateway logs

[ ] Application access logs

[ ] CDN logs (if applicable)


Verification period:


Recommended:

7-30 days



Check:


Legacy:


/api/*


Replacement:


/api/v1/*



====================================================
TASK 2
====================================================


Create Traffic Evidence Collector.



Create:


scripts/phase11_1_4_production_traffic_evidence.py



Requirements:


Input:


- log files
- exported CSV
- JSON logs


Analyze:


Count:


Legacy requests:

/api/


Django requests:

/api/v1/


Output:


JSON report:



Example:


{
 "period":"2026-01-01_to_2026-01-30",
 "legacy_requests":0,
 "replacement_requests":1000,
 "unknown_clients":0,
 "safe_to_decommission":true
}



====================================================
TASK 3
====================================================


Create Client Evidence Report.



Create:


docs/migration/PRODUCTION_CLIENT_DEPENDENCY_REPORT.md



Include:


Client source:

Frontend

Mobile

Integration

Partner API

Scheduled jobs

Internal scripts



For each:


Client

Legacy API usage

Replacement API

Migration status



====================================================
TASK 4
====================================================


Create Evidence Validation Report.



Create:


docs/migration/PRODUCTION_TRAFFIC_EVIDENCE_REPORT.md



Include:


Verification period

Data sources

Logs checked

Legacy API count

Django API count

Unknown clients

Decision



Possible result:


READY_FOR_DECOMMISSION


or


KEEP_LEGACY_API_ACTIVE



====================================================
TASK 5
====================================================


Create Approval Package.



Create:


docs/migration/LEGACY_API_SHUTDOWN_APPROVAL_PACKAGE.md



Include:


Technical approval

Business approval

Rollback owner

Maintenance window

Traffic evidence summary

Final recommendation



====================================================
TASK 6
====================================================


Security Review.



Verify:


- credentials masked

- tokens removed

- customer data redacted

- logs treated read-only



====================================================
TASK 7
====================================================


Create Tests.



Create:


django_backend/tests/test_phase11_1_4_traffic_evidence.py



Test:


- legacy route detection

- api/v1 exclusion

- empty logs

- zero traffic decision

- unknown client detection



====================================================
TASK 8
====================================================


Testing.



Run:


python scripts/phase11_1_4_production_traffic_evidence.py


python manage.py check


pytest django_backend\tests\test_phase11_1_4_traffic_evidence.py


pytest


powershell -ExecutionPolicy Bypass -File scripts\run_migration_test.ps1



Expected:


Without production logs:


BLOCKED_SAFELY



With valid evidence:


READY_FOR_DECOMMISSION



====================================================
TASK 9
====================================================


Create Review Package.



Create:


docs/reviews/


PHASE_11.1.4_REVIEW_SUMMARY.md


PHASE_11.1.4_CHANGESET.patch



Include:


Objective

Evidence sources

Traffic result

Dependency result

Security review

Testing

Recommendation



====================================================
GIT REQUIREMENTS
====================================================


Create branch:


migration/phase-11.1.4-production-traffic-evidence



Commit:


git add .


git commit -m "feat: add production traffic evidence collection"



Create tag:


phase-11.1.4-traffic-evidence-ready



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

Legacy API traffic result


5.

Client dependency result


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