# Phase 6 - Sales / Quotation Migration

## Objective

Implement read-only Django ORM mapping for quotation data and prepare transaction-safe future write migration.

## Scope

- quote requests
- quote request items
- quote files
- quotation read repositories
- quotation service interface

## Dependencies

- Phase 4A catalog ORM approved
- Phase 5 CRM migration approved
- read-only protection available
- transaction strategy documented

## DO NOT

- Do not create quote write APIs
- Do not change public quote form
- Do not modify quote tables
- Do not migrate files
- Do not create business workflow changes

## Implementation Tasks

- Create sales/quotation app structure
- Create unmanaged quotation models
- Add FK relationships to customers/products/materials
- Create quotation repository adapters
- Create read-only service interface
- Add tests for quote header/items/files

## Testing Requirements

- `python manage.py check`
- `pytest`
- quote row count parity
- quote item relationship validation
- quote file path preservation
- read-only write-block validation

## Git Requirements

- Create phase branch
- Create checkpoint commit
- Commit final implementation
- Create phase tag

## Review Package Requirements

- `docs/reviews/PHASE_6_CHANGESET.patch`
- `docs/reviews/PHASE_6_REVIEW_SUMMARY.md`

## Expected Output

- Sales/quotation read-only ORM slice
- Relationship tests
- Review package ready
