# Phase 9 - API Cutover

## Objective

Cut over selected legacy API routes to Django only after ORM/service/API parity is proven.

## Scope

- versioned Django API
- compatibility adapter
- route switching
- contract tests
- rollback route

## Dependencies

- required ORM slices approved
- service layer approved
- API compatibility strategy approved
- contract tests available
- rollback strategy approved

## DO NOT

- Do not cut over all routes at once
- Do not remove legacy endpoints immediately
- Do not change response shape silently
- Do not cut over write APIs without transaction tests
- Do not cut over auth without security approval

## Implementation Tasks

- Select low-risk endpoint
- Compare legacy and Django responses
- Add compatibility adapter if needed
- Add contract tests
- Configure route/proxy/frontend switch
- Validate rollback

## Testing Requirements

- `python manage.py check`
- `pytest`
- contract tests
- API integration tests
- rollback smoke tests
- error response tests

## Git Requirements

- Create phase branch
- Create checkpoint commit
- Commit final implementation
- Create phase tag

## Review Package Requirements

- `docs/reviews/PHASE_9_CHANGESET.patch`
- `docs/reviews/PHASE_9_REVIEW_SUMMARY.md`

## Expected Output

- Approved endpoint cutover
- Contract test evidence
- Rollback path documented
- Review package ready
