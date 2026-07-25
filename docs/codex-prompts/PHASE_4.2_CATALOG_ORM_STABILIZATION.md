# TASK: Phase 4.2 - Catalog ORM Stabilization & Migration Readiness

Project:

mecprecision-vietnam

====================================================
SAVE PROMPT
====================================================

Save this prompt to:

docs/codex-prompts/

Filename:

PHASE_4.2_CATALOG_ORM_STABILIZATION.md

====================================================
STATUS
====================================================

Completed:

Phase 4 Catalog ORM

Phase 4.1 Catalog ORM Hardening

Approved:

- unmanaged ORM
- legacy database routing
- readonly protection
- testing fixture
- ADR system

====================================================
OBJECTIVE
====================================================

Prepare Catalog ORM as the standard pattern
for future migrations:

Phase 5 CRM

Phase 6 Sales

Phase 7 CMS

====================================================
RULES
====================================================

DO NOT:

- create API
- create serializers
- create CRUD
- write legacy database
- migrate data

ONLY:

- optimize ORM
- improve repository
- improve documentation
- improve tests

====================================================
GIT
====================================================

Create:

migration/phase-4.2-catalog-stabilization

Checkpoint:

git commit -m "checkpoint: before phase 4.2 catalog stabilization"

====================================================
TASK 1
====================================================

Review ORM queries.

Check:

- N+1 queries
- select_related
- prefetch_related
- unnecessary queries

Create:

docs/reviews/CATALOG_QUERY_REVIEW.md

====================================================
TASK 2
====================================================

Standardize repositories.

Ensure:

No direct ORM outside repository.

Create:

Repository pattern document.

====================================================
TASK 3
====================================================

Create:

docs/migration/CATALOG_MIGRATION_PLAYBOOK.md

Include:

- model pattern
- repository pattern
- service pattern
- test pattern
- common mistakes

====================================================
TASK 4
====================================================

Create ADR:

docs/architecture/adr/

ADR-008-catalog-orm-query-strategy.md

====================================================
TASK 5
====================================================

Add tests:

- query count
- relationship loading
- repository usage

====================================================
TASK 6
====================================================

Create:

docs/reviews/PHASE_4.2_REVIEW_SUMMARY.md

Create:

docs/reviews/PHASE_4.2_CHANGESET.patch

Commit:

git commit -m "refactor: stabilize catalog orm foundation"

Tag:

phase-4.2-catalog-stabilization

====================================================

FINAL STATUS:

WAITING FOR ARCHITECT REVIEW

DO NOT START PHASE 5.
