# Migration Phase Testing Standard

## Purpose

Define mandatory validation before phase approval.

Every migration phase must run the same validation workflow before architecture review. This keeps the migration safe, repeatable and easy to compare across phases.

## Test Levels

### Level 1

Django System Check

Command:

```powershell
python manage.py check
```

Purpose:

- Validate Django settings.
- Detect invalid app/model configuration.
- Catch framework-level issues before running tests.

### Level 2

Current Module Tests

Example:

```powershell
pytest apps/catalog/tests
```

Purpose:

- Validate the module currently being migrated.
- Confirm model mapping, repositories, services and relationships for the active phase.

### Level 3

Regression Tests

Run all migrated modules:

- catalog
- crm
- sales
- cms

Purpose:

- Make sure a new phase does not break earlier migrated modules.
- Keep read-only ORM patterns consistent across modules.

### Level 4

Database Safety Tests

Verify:

- no legacy writes
- no unexpected migrations
- no schema changes

Purpose:

- Protect `backend/database/mecprecision.sqlite`.
- Confirm tests use fixture copies instead of writing to the source legacy database.
- Confirm unmanaged models remain read-only.

### Level 5

Review Package Validation

Required files:

- `PHASE_X_REVIEW_SUMMARY.md`
- `PHASE_X_CHANGESET.patch`

Purpose:

- Give architecture reviewers one summary and one Git diff package.
- Keep Git history as the source of truth.

## Standard Command

Run from the project root:

```powershell
.\scripts\run_migration_test.ps1
```

The script stops on the first failure. If everything passes, it prints:

```text
MIGRATION TEST PASSED
```
