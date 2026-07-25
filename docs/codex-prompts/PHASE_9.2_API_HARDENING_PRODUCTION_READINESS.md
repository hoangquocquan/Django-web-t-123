# TASK: Phase 9.2 - API Hardening & Production Readiness


Project:

mecprecision-vietnam



====================================================
SAVE THIS PROMPT
====================================================


Save this entire task specification into:


C:\Users\hoang\Documents\Codex\mecprecision-vietnam\docs\codex-prompts


Filename:


PHASE_9.2_API_HARDENING_PRODUCTION_READINESS.md



====================================================
STATUS
====================================================


Completed:


Phase 9 - API Health Cutover

Phase 9.1 - Business API Cutover



Approved capabilities:


- Django API routing
- Business read-only APIs
- Service based architecture
- Repository boundaries
- Legacy database read-only access



====================================================
OBJECTIVE
====================================================


Harden Django API layer before:

Phase 10 - Database Ownership Migration.



Goal:


Make API layer production-ready
without changing database ownership.



====================================================
IMPORTANT RULES
====================================================


DO NOT:


- migrate database
- change managed=False models
- write to legacy database
- shutdown legacy system
- enable public write APIs
- implement full authentication cutover



ONLY:


- improve API reliability
- improve API security
- improve API documentation
- improve API performance
- create production readiness checks



====================================================
READ DOCUMENTS FIRST
====================================================


Before implementation read:


docs/testing/PHASE_TESTING_STANDARD.md


docs/migration/API_CUTOVER_STRATEGY.md


docs/migration/API_CUTOVER_ROLLBACK_PLAN.md


docs/security/API_SECURITY_REVIEW.md


docs/api/API_CUTOVER_MATRIX.md


docs/architecture/adr/



====================================================
TASK 1
====================================================


API Documentation.



Create:


docs/api/API_REFERENCE.md



Include:


- endpoint list
- HTTP methods
- request format
- response format
- permissions
- legacy dependency
- migration status



Create:


docs/api/API_VERSIONING_STRATEGY.md



Include:


- /api/v1 policy
- backward compatibility
- future version strategy



====================================================
TASK 2
====================================================


OpenAPI Preparation.



Create:


docs/api/OPENAPI_READINESS.md



Include:


- serializer coverage
- schema requirements
- documentation gaps
- future Swagger integration plan



DO NOT install unnecessary packages.



====================================================
TASK 3
====================================================


API Performance Review.



Create:


docs/performance/API_PERFORMANCE_REVIEW.md



Review:


- query count
- N+1 queries
- pagination requirement
- large dataset handling
- response time baseline



Add tests for:


- query count
- pagination
- serializer efficiency



====================================================
TASK 4
====================================================


API Security Hardening.



Create:


docs/security/API_SECURITY_HARDENING.md



Review:


- authentication boundary
- permission enforcement
- sensitive fields
- readonly protection
- CSRF considerations
- rate limit requirements



Implement:


- stronger readonly permission tests
- sensitive data exposure tests



====================================================
TASK 5
====================================================


API Monitoring Preparation.



Create:


docs/operations/API_MONITORING_PLAN.md



Include:


- request logging
- error tracking
- health monitoring
- metrics
- alert requirements



DO NOT deploy monitoring tools.



====================================================
TASK 6
====================================================


API Test Improvement.



Add tests:


- endpoint availability
- permission tests
- response schema tests
- invalid request handling
- regression tests



Required command:


python manage.py check


pytest


.\scripts\run_migration_test.ps1



Expected:


All tests PASS.



====================================================
TASK 7
====================================================


Create API Production Checklist.



Create:


docs/operations/API_PRODUCTION_READINESS_CHECKLIST.md



Checklist:


Architecture

Security

Performance

Testing

Monitoring

Rollback

Documentation



====================================================
TASK 8
====================================================


Create Review Package.



Create:


docs/reviews/


PHASE_9.2_REVIEW_SUMMARY.md


PHASE_9.2_CHANGESET.patch



Summary:


Objective

Changes

API impact

Security impact

Performance impact

Testing results

Risks

Recommendation



====================================================
GIT REQUIREMENTS
====================================================


Create branch:


migration/phase-9.2-api-hardening



Commit:


git add .


git commit -m "feat: harden api production readiness"



Create tag:


phase-9.2-api-hardening-complete



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

Documentation created


5.

Tests result


6.

Review package location


7.

Git tag



FINAL STATUS:


WAITING FOR ARCHITECT REVIEW


STOP.

DO NOT START PHASE 10.