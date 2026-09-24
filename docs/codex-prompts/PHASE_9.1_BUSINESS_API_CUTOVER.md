# TASK: Phase 9.1 - Business API Cutover


Project:

mecprecision-vietnam



====================================================
SAVE THIS PROMPT
====================================================


Save this entire task specification into:


C:\Users\hoang\Documents\Codex\mecprecision-vietnam\docs\codex-prompts


Filename:


PHASE_9.1_BUSINESS_API_CUTOVER.md



====================================================
STATUS
====================================================


Completed:


Phase 9 - API Health Cutover



Approved:


- Django API routing
- compatibility adapter pattern
- health endpoint cutover
- rollback documentation
- regression testing



====================================================
OBJECTIVE
====================================================


Extend Phase 9 from health API validation
to business domain API readiness.



Goal:


Django becomes the application API layer
for migrated business modules.



====================================================
IMPORTANT RULES
====================================================


DO NOT:


- migrate database ownership
- change managed=False models
- write to legacy database
- shutdown legacy system
- change production traffic immediately
- create destructive migrations



ONLY:


- create read-only business APIs
- preserve legacy contracts
- validate service architecture
- prepare application cutover



====================================================
READ REQUIRED DOCUMENTS
====================================================


Before implementation read:


docs/testing/PHASE_TESTING_STANDARD.md


docs/migration/API_CUTOVER_STRATEGY.md


docs/migration/API_CUTOVER_ROLLBACK_PLAN.md


docs/migration/CATALOG_MIGRATION_PLAYBOOK.md


docs/migration/CRM_MIGRATION_CHECKLIST.md


docs/migration/SALES_MIGRATION_PLAYBOOK.md


docs/architecture/adr/



====================================================
ARCHITECTURE RULE
====================================================


API layer MUST follow:


API View


    ↓


Service Layer


    ↓


Repository Layer


    ↓


Django ORM


    ↓


Legacy Database



DO NOT:


Put business logic inside API views.



====================================================
TASK 1
====================================================


Create API foundation structure:


django_backend/apps/api/


Structure:


api/

├── urls.py

├── permissions.py

├── serializers/

├── views/

└── tests/



Purpose:


Central API routing layer.



====================================================
TASK 2
====================================================


Create read-only APIs for Catalog.



Endpoints:


GET /api/v1/catalog/products/

GET /api/v1/catalog/products/<id>/


GET /api/v1/catalog/categories/

GET /api/v1/catalog/materials/



Requirements:


- use existing catalog services
- no direct ORM access
- preserve read-only behavior



====================================================
TASK 3
====================================================


Create read-only APIs for CRM.



Endpoints:


GET /api/v1/crm/customers/

GET /api/v1/crm/customers/<id>/


GET /api/v1/crm/contact-requests/



Requirements:


- use CRM service layer
- no customer data modification



====================================================
TASK 4
====================================================


Create read-only APIs for Sales.



Endpoints:


GET /api/v1/sales/quotes/

GET /api/v1/sales/quotes/<id>/


GET /api/v1/sales/quotes/<id>/files/



Requirements:


- use Sales service
- preserve quotation snapshot behavior
- no write operations



====================================================
TASK 5
====================================================


Create read-only APIs for CMS.



Endpoints:


GET /api/v1/cms/pages/

GET /api/v1/cms/pages/<slug>/


GET /api/v1/cms/menu/



Requirements:


- preserve menu hierarchy
- preserve content structure



====================================================
TASK 6
====================================================


Authentication API preparation.



DO NOT implement login cutover.



Only prepare:


GET /api/v1/auth/profile/


GET /api/v1/auth/permissions/



Requirements:


- no password exposure
- no session mutation
- no token changes



====================================================
TASK 7
====================================================


API Documentation.



Create:


docs/api/API_CUTOVER_MATRIX.md



Include:


Domain

Endpoint

Service used

Read/Write status

Legacy dependency

Migration status



====================================================
TASK 8
====================================================


Security Review.



Create:


docs/security/API_SECURITY_REVIEW.md



Review:


- permission handling
- authentication boundary
- sensitive data exposure
- readonly enforcement



====================================================
TASK 9
====================================================


Testing.



Must run:


python manage.py check


pytest


.\scripts\run_migration_test.ps1



Required tests:


- API endpoint tests
- permission tests
- readonly tests
- regression tests



====================================================
TASK 10
====================================================


Create review package.



Create:


docs/reviews/


PHASE_9.1_REVIEW_SUMMARY.md


PHASE_9.1_CHANGESET.patch



Summary must include:


Objective

Endpoints created

Architecture impact

Database impact

Security review

Tests

Risks

Recommendation



====================================================
GIT
====================================================


Create branch:


migration/phase-9.1-business-api-cutover



Commit:


git add .


git commit -m "feat: add business api cutover"



Create tag:


phase-9.1-business-api-cutover-complete



====================================================
FINAL OUTPUT
====================================================


Return:


1.

Branch name


2.

Base commit hash


3.

Final commit hash


4.

API endpoints created


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