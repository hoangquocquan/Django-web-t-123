# Phase 4A - Catalog Read-Only ORM

## Objective

Implement read-only unmanaged Django ORM models for catalog data.

## Scope

- categories
- materials
- machines
- manufacturing processes
- capabilities
- products
- product images
- product specs
- catalog relationship tables

## Dependencies

- Phase 3 database mapping approved
- Phase 3.1 ORM rules approved
- Phase 3.2 ORM readiness approved
- Django foundation available

## DO NOT

- Do not modify legacy database
- Do not create migrations
- Do not run migrate
- Do not create API endpoints
- Do not create serializers
- Do not create write behavior

## Implementation Tasks

- Configure `legacy` database alias
- Create read-only base model
- Create catalog app
- Add unmanaged catalog models
- Add repository adapters
- Add service interface
- Add read-only tests

## Testing Requirements

- `python manage.py check`
- `pytest`
- verify legacy database read access
- verify model table mapping
- verify relationships
- verify write operations are blocked

## Git Requirements

- Create phase branch
- Create checkpoint commit before work
- Commit final implementation
- Create phase completion tag

## Review Package Requirements

- `docs/reviews/PHASE_4A_CHANGESET.patch`
- `docs/reviews/PHASE_4A_REVIEW_SUMMARY.md`

## Expected Output

- Catalog unmanaged ORM models
- Repository adapters
- Service interface
- Passing tests
- Review package ready
