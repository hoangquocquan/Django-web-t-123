# TASK: Phase 4.1 - Catalog ORM Hardening & Implementation Standardization


Project:

mecprecision-vietnam


====================================================
IMPORTANT: SAVE THIS PROMPT
====================================================


Before execution:

Save this entire task specification into:


docs/codex-prompts/


Filename:


PHASE_4.1_CATALOG_ORM_HARDENING.md



Purpose:

Maintain migration history and allow future reuse.



====================================================
STATUS
====================================================


Phase 4A:

Catalog Read-Only Unmanaged ORM


Status:

APPROVED WITH FIXES



Existing implementation:


- unmanaged Django ORM models
- LegacyReadOnlyModel
- repository layer
- service layer
- tests



====================================================
OBJECTIVE
====================================================


Harden Phase 4A implementation before starting:


Phase 4B - CRM Read-Only ORM



Resolve:


1. Composite primary key implementation clarity

2. Legacy database test fixture

3. Database routing validation

4. ORM implementation standardization

5. Architecture decision records



====================================================
STRICT RULES
====================================================


DO NOT:


- create new business models
- migrate data
- create API
- create serializers
- modify legacy database
- change catalog business logic


ONLY:


- improve infrastructure
- improve tests
- improve documentation
- improve architecture consistency



====================================================
GIT WORKFLOW
====================================================


Create branch:


git checkout develop

git checkout -b migration/phase-4.1-catalog-orm-hardening



Before starting:


git add .

git commit -m "checkpoint: before phase 4.1 catalog orm hardening"



Record:


BASE_COMMIT_HASH



====================================================
TASK 1: REVIEW COMPOSITE PRIMARY KEY IMPLEMENTATION
====================================================


Analyze current models:


- ProductMaterial
- ProductProcess
- CapabilityMachine


Create:


docs/reviews/COMPOSITE_KEY_IMPLEMENTATION_REVIEW.md



Include:


## Django Version


## Current Implementation


## Tables Using Composite Keys


## Query Behavior


## Limitations


## Production Risks


## Recommendation



Verify:


- Does current Django version support CompositePrimaryKey?
- Is implementation production safe?
- Are relationships working?



If problems exist:


Document recommended solution.



====================================================
TASK 2: CREATE LEGACY DATABASE TEST FIXTURE
====================================================


Problem:


Current tests depend on local:


backend/database/mecprecision.sqlite



Create isolated test fixture:


tests/fixtures/legacy_database/



Copy database for testing only.



Create:


scripts/


copy_legacy_database_for_test.py



Purpose:


Prepare safe database copy for CI/test.



Rules:


Never modify original database.



Update tests to use fixture.



====================================================
TASK 3: DATABASE ROUTING VALIDATION
====================================================


Review:


DATABASES configuration


Add tests:


tests/test_database_routing.py



Verify:


1.


Catalog models use:


using("legacy")



2.


Default database is not used accidentally.



3.


Write attempts against legacy are blocked.



====================================================
TASK 4: CREATE ORM IMPLEMENTATION STANDARD
====================================================


Create:


docs/migration/PHASE_4_IMPLEMENTATION_RULES.md



Purpose:


Standard pattern for all future ORM phases.



Include:



# Model Rules


Example:


class Product(LegacyReadOnlyModel):

    class Meta:

        managed=False

        db_table="products"



# Repository Rules


All queries:


.objects.using("legacy")



# Service Rules


Service calls Repository only.



# Forbidden Patterns


DO NOT:


Product.objects.all()


inside API/service.



DO NOT:


write business logic inside models.



====================================================
TASK 5: CREATE ARCHITECTURE DECISION RECORDS
====================================================


Create:


docs/architecture/adr/



Add:


ADR-005-readonly-legacy-orm.md



Decision:


Use unmanaged Django ORM for legacy migration.



Add:


ADR-006-composite-key-strategy.md



Decision:


How composite key tables are handled.



Add:


ADR-007-multi-database-routing.md



Decision:


default database vs legacy database.



====================================================
TASK 6: IMPROVE TEST COVERAGE
====================================================


Add tests:


## Legacy database isolation


## Repository database usage


## Read-only enforcement


## Composite relationship access


## Fixture loading



Expected:


All tests PASS.



====================================================
TASK 7: UPDATE MIGRATION DOCUMENTATION
====================================================


Update:


docs/migration/


Add:


Phase 4.1 notes into:


MIGRATION_ROADMAP.md



Update:


PHASE_4_IMPLEMENTATION_RULES.md



====================================================
TASK 8: CREATE PHASE 4.1 REVIEW PACKAGE
====================================================


Create:


docs/reviews/


PHASE_4.1_REVIEW_SUMMARY.md



Include:


# Phase 4.1 Review Summary


## Objective


## Problems Resolved


## Files Changed


## Architecture Decisions


## Database Impact


## Testing Result


## Risks Remaining


## Recommendation


Status:


WAITING FOR ARCHITECT REVIEW



====================================================
GIT DIFF PACKAGE
====================================================


After completion:


Commit:


git add .

git commit -m "fix: harden catalog readonly orm implementation"



Generate:


docs/reviews/PHASE_4.1_CHANGESET.patch



Command:


git diff BASE_COMMIT_HASH FINAL_COMMIT_HASH \
> docs/reviews/PHASE_4.1_CHANGESET.patch



Create tag:


git tag phase-4.1-catalog-orm-hardening-complete



====================================================
FINAL OUTPUT
====================================================


Return:


1. Branch name

2. Base commit hash

3. Final commit hash

4. Prompt file location

5. Documents created

6. ADR created

7. Test result

8. Diff package location



Final status:


WAITING FOR ARCHITECT REVIEW



STOP.

DO NOT START PHASE 4B.