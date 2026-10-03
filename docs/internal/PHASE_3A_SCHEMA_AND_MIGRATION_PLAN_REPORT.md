# Phase 3A Schema and Migration Plan Report

## Verdict

`PASS`

The Phase 1/2 checkpoint was created successfully before Phase 3A, and Phase 3A
then completed a documentation-only persistence design. No model, migration,
database data, API behavior, or frontend code was changed.

Conclusion: `READY_FOR_PHASE_3B_AFTER_OWNER_APPROVAL`.

## Checkpoint evidence

- Commit: `41753f485f437ecde2cf19e3101d856e7e96a54c`
- Subject: `chore: stabilize project and define MVP business contract`
- Commit count from the pre-task HEAD: exactly one.
- Files in the checkpoint: 19, all belonging to the audited Phase 1
  stabilization/full-test closure or Phase 2 business contract.
- No push was performed.
- Working tree was clean immediately after the checkpoint.

Pre-commit gates:

- Django system check: 0 issues.
- Migration drift: `No changes detected`.
- Full backend suite: `99 passed, 140 skipped`, 0 failed/errors.
- Frontend locked install: passed; non-fatal registry metadata warning only.
- Frontend production build: passed with Vite 8.0.5, 16 modules transformed.
- Three workflow YAML files parsed successfully.
- Cached diff whitespace and secret-signature checks: passed after removing
  three trailing spaces in the Phase 2 specification.
- No model, migration, seed/data, or SQLite artifact entered the checkpoint.

## Phase 3A output

The detailed, authoritative design is
`docs/database/PHASE_3A_SCHEMA_AND_MIGRATION_PLAN.md`. It includes:

- a complete current-model inventory across foundation, business core, catalog,
  CRM, sales, transaction domain, and knowledge;
- exact managed/unmanaged table ownership, keys, relations, consumers, current
  constraints/indexes, router behavior, and migration graph;
- one definitive source decision for all 16 required domain concepts;
- target tables, fields, relations, invariants, indexes, and constraints;
- an additive/backfill/constraint/cutover migration sequence;
- explicit handling for ambiguous legacy quotations/orders without fabricated
  business evidence;
- old-consumer compatibility and API/UI write cutoffs;
- rollback, verification, tests, risks, and stop conditions.

## Final canonical choices

- Extend `BusinessCustomer` and `BusinessProduct`.
- Create managed `BusinessMaterial`.
- Create RFQ, RFQLine, RFQDocument, and TechnicalReview in `sales`.
- Extend current `SalesQuotation` and `SalesQuotationLine`; RFQ is the quotation
  family boundary and each row is one revision.
- Create separate immutable approval and customer-decision records.
- Extend current `TransactionOrder` and `TransactionOrderItem`.
- Create append-only OrderProgressEvent and AuditEvent.
- Extend Foundation Role/Permission with action-specific permissions.
- Retain all unmanaged catalog/CRM/sales tables as explicit read-only legacy
  sources; retain fragmented managed history tables for later deprecation.

## Safety confirmation

Phase 3A ran only read-only inspection commands and created these two Markdown
documents. `showmigrations --plan` was used only to inspect the graph; `migrate`
was not run. No migration file was generated. No legacy artifact was enabled or
read, no external service was contacted, and no repository outside the Django
project was accessed.
