# Phase 5 - CRM Migration

## Objective

Implement read-only Django ORM mapping for CRM data and prepare CRM service/repository boundaries.

## Scope

- customers
- customer notes
- contact requests
- CRM read-only repositories
- CRM validation tests

## Dependencies

- Phase 4A catalog ORM approved
- database mapping approved
- read-only ORM protection available
- multi-database strategy available

## DO NOT

- Do not create contact write APIs
- Do not change contact form behavior
- Do not modify legacy CRM database tables
- Do not migrate data
- Do not replace legacy CRM services

## Implementation Tasks

- Create CRM app structure
- Create unmanaged CRM models
- Create CRM repository adapters
- Create read-only CRM service interface
- Add relationship/data integrity tests
- Document CRM limitations

## Testing Requirements

- `python manage.py check`
- `pytest`
- row count parity for CRM tables
- customer/contact relationship validation
- read-only protection validation

## Git Requirements

- Create phase branch
- Create checkpoint commit
- Commit final implementation
- Create phase tag

## Review Package Requirements

- `docs/reviews/PHASE_5_CHANGESET.patch`
- `docs/reviews/PHASE_5_REVIEW_SUMMARY.md`

## Expected Output

- CRM read-only ORM slice
- Repository/service boundary
- Passing tests
- Review package ready
