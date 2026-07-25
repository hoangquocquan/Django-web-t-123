# TASK: Phase 5.1 - CRM Hardening & Migration Governance

Project:

mecprecision-vietnam

====================================================
SAVE THIS PROMPT
====================================================

Before execution:

Save this entire task specification into:

docs/codex-prompts/

Filename:

PHASE_5.1_CRM_HARDENING_AND_GOVERNANCE.md

Purpose:

Maintain migration history and provide reusable CRM migration standards.

====================================================
STATUS
====================================================

Completed:

Phase 5 - CRM Migration

Approved:

- unmanaged ORM
- CRM repository layer
- CRM service layer
- legacy database routing
- read-only protection
- CRM tests

Status:

APPROVED WITH MINOR FOLLOW-UP

====================================================
OBJECTIVE
====================================================

Harden CRM implementation before:

Phase 6 - Sales / Quotation Migration

Goals:

1.

Create CRM migration governance documentation.

2.

Resolve customer/contact relationship strategy.

3.

Validate CRM data quality risks.

4.

Create CRM-specific ADR.

5.

Prepare CRM pattern for future modules.

====================================================
STRICT RULES
====================================================

DO NOT:

- create CRM API
- create serializers
- create CRUD write operations
- modify legacy database
- migrate customer data
- change existing CRM models without documentation

ONLY:

- documentation
- validation
- architecture decisions
- test improvements

====================================================
GIT WORKFLOW
====================================================

Create branch:

git checkout develop

git checkout -b migration/phase-5.1-crm-hardening

Create checkpoint:

git add .

git commit -m "checkpoint: before phase 5.1 crm hardening"

Record:

BASE_COMMIT_HASH

====================================================
TASK 1: CREATE CRM MIGRATION STRATEGY ADR
====================================================

Create:

docs/architecture/adr/

ADR-009-crm-migration-strategy.md

Include:

# ADR-009 CRM Migration Strategy

## Context

Legacy CRM tables:

- customers
- customer_notes
- contact_requests

## Decision

Use read-only unmanaged ORM migration pattern.

## Customer Relationship Strategy

Explain:

How future matching will work:

- email matching
- phone matching
- manual verification

## Consequences

Benefits:

Risks:

Future actions:

====================================================
TASK 2: CRM DATA QUALITY REVIEW
====================================================

Create:

docs/migration/CRM_DATA_QUALITY_REVIEW.md

Analyze:

customers:

- duplicate records
- missing fields
- invalid email
- invalid phone
- incomplete information

customer_notes:

- orphan records
- missing customers

contact_requests:

- missing customer relation
- duplicate requests

For each:

Issue:

Impact:

Recommendation:

DO NOT modify data.

====================================================
TASK 3: CONTACT REQUEST RELATIONSHIP STRATEGY
====================================================

Create:

docs/migration/CRM_CONTACT_RELATIONSHIP_STRATEGY.md

Analyze:

Current:

contact_requests

has no customer foreign key.

Define future strategy:

Option A:

Email matching

Option B:

Phone matching

Option C:

Manual customer linking

Option D:

New relationship table

Recommend approach.

DO NOT create database changes.

====================================================
TASK 4: CUSTOMER NOTES VALIDATION
====================================================

Analyze:

customer_notes

Create:

docs/migration/CRM_NOTES_VALIDATION.md

Include:

- table structure
- relationship mapping
- current data status
- testing limitation
- future migration considerations

====================================================
TASK 5: IMPROVE CRM TEST COVERAGE
====================================================

Add tests:

1.

CRM repository uses legacy database.

2.

Customer relationship loading.

3.

Customer notes relationship.

4.

Contact request mapping.

5.

Read-only protection.

6.

Fixture based testing.

Run:

python manage.py check

pytest

====================================================
TASK 6: UPDATE MIGRATION DOCUMENTATION
====================================================

Update:

docs/migration/MIGRATION_ROADMAP.md

Add:

Phase 5.1

Status:

Completed after approval

Update:

CRM_MIGRATION_LIMITATIONS.md

====================================================
TASK 7: CREATE CRM MIGRATION CHECKLIST
====================================================

Create:

docs/migration/CRM_MIGRATION_CHECKLIST.md

Include:

Before Phase 6:

[ ] CRM ADR completed

[ ] Data quality reviewed

[ ] Contact strategy documented

[ ] Tests passing

[ ] Risks documented

====================================================
TASK 8: CREATE REVIEW PACKAGE
====================================================

Create:

docs/reviews/

PHASE_5.1_REVIEW_SUMMARY.md

Include:

# Phase 5.1 Review Summary

## Objective

## Problems Resolved

## ADR Created

## Documents Created

## Database Impact

## API Impact

## Tests

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

git commit -m "docs: harden crm migration strategy"

Generate:

docs/reviews/PHASE_5.1_CHANGESET.patch

Command:

git diff BASE_COMMIT_HASH FINAL_COMMIT_HASH \
> docs/reviews/PHASE_5.1_CHANGESET.patch

Create tag:

git tag phase-5.1-crm-hardening-complete

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

Prompt file location

5.

Documents created

6.

ADR created

7.

Test result

8.

Diff package location

FINAL STATUS:

WAITING FOR ARCHITECT REVIEW

STOP.

DO NOT START PHASE 6.
