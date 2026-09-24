# TASK: Phase 9.3 - Migration Readiness Validation


Project:

mecprecision-vietnam



====================================================
SAVE THIS PROMPT
====================================================


Before implementation:


Save this task specification into:


C:\Users\hoang\Documents\Codex\mecprecision-vietnam\docs\codex-prompts


Filename:


PHASE_9.3_MIGRATION_READINESS_VALIDATION.md



====================================================
STATUS
====================================================


Completed:


Phase 9
API Health Cutover


Phase 9.1
Business API Cutover


Phase 9.2
API Hardening & Production Readiness



====================================================
OBJECTIVE
====================================================


Perform final migration readiness assessment
before Phase 10 Database Ownership Migration.



Goal:


Confirm Django application layer is ready
for database ownership transition.



====================================================
IMPORTANT RULES
====================================================


DO NOT:


- migrate database
- change managed=False models
- create schema migrations
- write to legacy database
- shutdown legacy system
- change production traffic



ONLY:


- audit
- document
- validate
- prepare migration plan



====================================================
READ REQUIRED DOCUMENTS
====================================================


Before implementation read:


docs/testing/PHASE_TESTING_STANDARD.md


docs/migration/API_CUTOVER_STRATEGY.md


docs/migration/API_CUTOVER_ROLLBACK_PLAN.md


docs/api/API_CUTOVER_MATRIX.md


docs/security/API_SECURITY_REVIEW.md


docs/api/API_REFERENCE.md


docs/architecture/adr/



====================================================
TASK 1
====================================================


Create Database Dependency Inventory.



Create:


docs/migration/DATABASE_DEPENDENCY_INVENTORY.md



Include:


- all Django apps
- models used
- database tables
- legacy database dependency
- read/write status
- migration priority



Cover:


Catalog

CRM

Sales

CMS

Accounts

API



====================================================
TASK 2
====================================================


Create Unmanaged Model Inventory.



Create:


docs/migration/UNMANAGED_MODEL_INVENTORY.md



Include:


For every model:


- app name
- model name
- table name
- managed status
- primary key
- foreign keys
- dependencies
- migration complexity



====================================================
TASK 3
====================================================


Create Database Migration Impact Assessment.



Create:


docs/migration/DATABASE_MIGRATION_IMPACT_ASSESSMENT.md



Include:


- schema risks
- data volume risks
- relationship risks
- constraint risks
- indexing risks
- downtime risks



====================================================
TASK 4
====================================================


Create Phase 10 Preparation Plan.



Create:


docs/migration/PHASE_10_PREPARATION_PLAN.md



Include:


- PostgreSQL migration approach
- backup strategy
- rollback strategy
- migration order
- validation steps
- cutover checklist



====================================================
TASK 5
====================================================


Create Data Ownership Matrix.



Create:


docs/migration/DATA_OWNERSHIP_MATRIX.md



Define:


Current:


Legacy database owner


Future:


Django database owner



For:


Catalog

CRM

Sales

CMS

Accounts



====================================================
TASK 6
====================================================


Create Migration Gate Checklist.



Create:


docs/migration/MIGRATION_READINESS_CHECKLIST.md



Checklist:


Application Layer:

[ ] API ready

[ ] Services ready

[ ] Repository boundaries confirmed


Database:

[ ] Inventory completed

[ ] Dependencies mapped

[ ] Backup strategy ready


Testing:

[ ] Regression passed

[ ] Rollback tested


Security:

[ ] Authentication boundary reviewed

[ ] Sensitive data protected



====================================================
TASK 7
====================================================


Run Validation Tests.



Execute:


python manage.py check


pytest


.\scripts\run_migration_test.ps1



Expected:


PASS



====================================================
TASK 8
====================================================


Create Review Package.



Create:


docs/reviews/


PHASE_9.3_REVIEW_SUMMARY.md


PHASE_9.3_CHANGESET.patch



Summary:


Objective

Inventory results

Migration readiness

Risks

Phase 10 recommendation



====================================================
GIT REQUIREMENTS
====================================================


Create branch:


migration/phase-9.3-readiness-validation



Commit:


git add .


git commit -m "docs: add migration readiness validation"



Create tag:


phase-9.3-readiness-complete



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

Documents created


5.

Testing result


6.

Review package location


7.

Git tag



FINAL STATUS:


WAITING FOR ARCHITECT REVIEW


STOP.

DO NOT START PHASE 10.