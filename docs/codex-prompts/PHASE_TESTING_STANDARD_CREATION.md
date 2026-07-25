# TASK: Create Migration Testing Standard

Project:

mecprecision-vietnam

====================================================
SAVE THIS PROMPT
====================================================

Save this prompt into:

C:\Users\hoang\Documents\Codex\mecprecision-vietnam\docs\codex-prompts

Filename:

PHASE_TESTING_STANDARD_CREATION.md

====================================================
OBJECTIVE
====================================================

Create a standard automated validation process
for all future migration phases.

The purpose:

Every Codex migration phase must run the same
testing workflow before architecture review.

====================================================
RULES
====================================================

DO NOT:

- modify business code
- change models
- change database
- create API

ONLY:

- create testing documentation
- create test automation script

====================================================
CREATE DOCUMENT
====================================================

Create:

docs/testing/PHASE_TESTING_STANDARD.md

Content:

# Migration Phase Testing Standard

## Purpose

Define mandatory validation before phase approval.

## Test Levels

### Level 1

Django System Check

Command:

python manage.py check

### Level 2

Current Module Tests

Example:

pytest apps/catalog/tests

### Level 3

Regression Tests

Run all migrated modules:

catalog

crm

sales

cms

### Level 4

Database Safety Tests

Verify:

- no legacy writes
- no unexpected migrations
- no schema changes

### Level 5

Review Package Validation

Required files:

PHASE_X_REVIEW_SUMMARY.md

PHASE_X_CHANGESET.patch

====================================================
CREATE POWERSHELL SCRIPT
====================================================

Create:

scripts/run_migration_test.ps1

Purpose:

One command runs full migration validation.

Script must execute:

Step 1:

python manage.py check

Step 2:

pytest django_backend/apps/catalog/tests

Step 3:

pytest django_backend/apps/crm/tests

Step 4:

pytest django_backend/apps/sales/tests

Step 5:

pytest django_backend/apps/cms/tests

Step 6:

pytest

If any step fails:

Stop execution.

Return failure status.

If all pass:

Return:

MIGRATION TEST PASSED

====================================================
CREATE TEST REPORT TEMPLATE
====================================================

Create:

docs/testing/MIGRATION_TEST_REPORT_TEMPLATE.md

Include:

Phase:

Date:

Commit:

System Check:

Module Tests:

Regression Tests:

Database Safety:

Result:

====================================================
UPDATE ROADMAP
====================================================

Update:

docs/migration/MIGRATION_ROADMAP.md

Add:

Migration Testing Standard Completed

====================================================
GIT
====================================================

Commit:

git add .

git commit -m "docs: add migration testing standard"

Create tag:

testing-standard-ready

====================================================
FINAL OUTPUT
====================================================

Return:

1. Files created

2. Script location

3. Test command usage

4. Commit hash

5. Tag

STATUS:

MIGRATION TESTING STANDARD READY
