# TASK: Phase 6.1 - Sales Quotation Hardening & Transaction Governance

Project:

mecprecision-vietnam

====================================================
SAVE THIS PROMPT
====================================================

Before execution:

Save this entire task specification into:

docs/codex-prompts/

Filename:

PHASE_6.1_SALES_QUOTATION_HARDENING.md

Purpose:

Maintain migration history and define Sales domain governance.

====================================================
STATUS
====================================================

Completed:

Phase 6 - Sales / Quotation Migration

Approved:

- unmanaged ORM models
- sales repository layer
- sales service layer
- legacy database routing
- read-only protection
- sales query tests

Status:

APPROVED WITH MINOR FOLLOW-UP

====================================================
OBJECTIVE
====================================================

Harden Sales / Quotation architecture before:

Phase 7 - CMS Migration

Goals:

1.

Create Sales architecture decisions.

2.

Define quotation transaction strategy.

3.

Define quotation snapshot strategy.

4.

Review file lifecycle handling.

5.

Prepare Sales migration playbook.

====================================================
STRICT RULES
====================================================

DO NOT:

- create Sales API
- create serializers
- create CRUD write operations
- modify legacy database
- migrate quotation data
- change pricing data
- introduce write transactions

ONLY:

- architecture documentation
- validation
- test improvements
- ADR creation

====================================================
GIT WORKFLOW
====================================================

Create branch:

git checkout develop

git checkout -b migration/phase-6.1-sales-hardening

Create checkpoint:

git add .

git commit -m "checkpoint: before phase 6.1 sales hardening"

Record:

BASE_COMMIT_HASH

====================================================
TASK 1: CREATE SALES ADR
====================================================

Create:

docs/architecture/adr/

ADR-010-sales-quotation-strategy.md

Include:

# ADR-010 Sales Quotation Strategy

## Context

Legacy sales tables:

- quote_requests
- quote_request_items
- quote_files

Dependencies:

CRM:

- customers

Catalog:

- products
- materials

## Decision

Use read-only unmanaged ORM pattern.

## Domain Boundary

Define:

CRM responsibility:

Customer ownership

Catalog responsibility:

Product/material ownership

Sales responsibility:

Quotation lifecycle

## Consequences

Benefits:

Risks:

Future actions:

====================================================
TASK 2: CREATE QUOTATION SNAPSHOT STRATEGY
====================================================

Create:

docs/migration/QUOTATION_SNAPSHOT_STRATEGY.md

Analyze:

Problem:

Products and prices change over time.

Quotation history must preserve historical state.

Define future snapshot fields:

Example:

Quote Item:

- product name snapshot
- material snapshot
- specification snapshot
- unit price snapshot
- quantity snapshot

Define:

When snapshot happens:

- quote creation
- quote approval
- quote conversion

DO NOT implement database changes.

====================================================
TASK 3: CREATE SALES TRANSACTION STRATEGY
====================================================

Create:

docs/migration/SALES_TRANSACTION_STRATEGY.md

Define future write transaction boundary.

Analyze:

Future workflow:

Customer creation/linking

↓

Quote creation

↓

Quote items creation

↓

File metadata creation

Define:

Atomic transaction requirement.

Include:

- database transaction
- rollback strategy
- failure scenarios
- external file handling

====================================================
TASK 4: REVIEW FILE LIFECYCLE STRATEGY
====================================================

Create:

docs/migration/QUOTE_FILE_LIFECYCLE_STRATEGY.md

Analyze:

Current:

quote_files

Fields:

- path
- filename
- metadata

Define future:

- upload flow
- storage migration
- cleanup strategy
- orphan file handling

Rules:

Do not migrate physical files.

====================================================
TASK 5: SALES DATA QUALITY REVIEW
====================================================

Create:

docs/migration/SALES_DATA_QUALITY_REVIEW.md

Analyze:

quote_requests:

- missing customer references
- invalid status
- incomplete fields

quote_request_items:

- invalid product references
- missing quantities
- pricing issues

quote_files:

- missing paths
- invalid references

Do not modify data.

====================================================
TASK 6: CREATE SALES MIGRATION PLAYBOOK
====================================================

Create:

docs/migration/SALES_MIGRATION_PLAYBOOK.md

Include:

Standard pattern:

Model

↓

Repository

↓

Service

↓

Transaction boundary

↓

Tests

Include:

- common mistakes
- future write migration rules
- dependency rules

====================================================
TASK 7: IMPROVE TEST COVERAGE
====================================================

Add tests:

1.

Sales repository uses legacy database.

2.

Quotation relationship loading.

3.

Customer reference validation.

4.

Product/material reference validation.

5.

File path preservation.

6.

Read-only protection.

7.

Fixture-based testing.

Run:

python manage.py check

pytest

====================================================
TASK 8: UPDATE ROADMAP
====================================================

Update:

docs/migration/MIGRATION_ROADMAP.md

Add:

Phase 6.1

Status:

Completed after approval

====================================================
TASK 9: CREATE REVIEW PACKAGE
====================================================

Create:

docs/reviews/

PHASE_6.1_REVIEW_SUMMARY.md

Include:

# Phase 6.1 Review Summary

## Objective

## Problems Resolved

## ADR Created

## Documents Created

## Database Impact

## API Impact

## Transaction Strategy

## Snapshot Strategy

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

git commit -m "docs: harden sales quotation strategy"

Generate:

docs/reviews/PHASE_6.1_CHANGESET.patch

Command:

git diff BASE_COMMIT_HASH FINAL_COMMIT_HASH \
> docs/reviews/PHASE_6.1_CHANGESET.patch

Create tag:

git tag phase-6.1-sales-hardening-complete

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

DO NOT START PHASE 7.
