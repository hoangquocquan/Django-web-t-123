# Phase 7 - CMS Migration

## Objective

Implement read-only Django ORM mapping for CMS/content management data.

## Scope

- CMS pages
- menu items
- banners
- newsletter subscribers
- CMS read repositories
- CMS read services

## Dependencies

- Phase 4A catalog ORM approved
- content/media boundaries approved
- auth migration boundary respected
- read-only protection available

## DO NOT

- Do not create CMS write CRUD
- Do not change admin UI behavior
- Do not migrate uploads
- Do not modify menu/page/banner tables
- Do not migrate authentication

## Implementation Tasks

- Create CMS/content app structure
- Create unmanaged CMS models
- Handle self-referential menu relationship
- Create read-only repositories
- Add service interface
- Add tests for pages, menus, banners, newsletter

## Testing Requirements

- `python manage.py check`
- `pytest`
- table count parity
- nested menu relationship validation
- read-only protection validation

## Git Requirements

- Create phase branch
- Create checkpoint commit
- Commit final implementation
- Create phase tag

## Review Package Requirements

- `docs/reviews/PHASE_7_CHANGESET.patch`
- `docs/reviews/PHASE_7_REVIEW_SUMMARY.md`

## Expected Output

- CMS read-only ORM slice
- Relationship tests
- Review package ready
