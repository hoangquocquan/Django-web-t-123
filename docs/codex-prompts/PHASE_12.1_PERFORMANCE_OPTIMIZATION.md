# Phase 12.1 - Performance Optimization

## Status

PLANNED

## Objective

Optimize production performance after Django owns application behavior.

## Dependencies

- Production traffic baseline
- API performance review
- Database indexes reviewed

## Scope

- query optimization
- caching strategy
- indexing
- load testing
- response optimization

## DO NOT

- Do not add cache without invalidation strategy.
- Do not change indexes without migration review.
- Do not optimize blindly without measurements.

## Implementation Tasks

- Collect p50/p95/p99 latency.
- Review slow queries.
- Add or tune indexes.
- Design caching strategy.
- Run load tests.
- Optimize serializer/response shape if needed.

## Testing Requirements

- Query count tests.
- Load test report.
- Regression tests.
- Cache invalidation tests if cache is implemented.

## Security Requirements

- Do not cache private/auth-sensitive payloads publicly.
- Protect performance logs.

## Database Impact

Possible index migrations after approval.

## Rollback Strategy

Rollback indexes/cache configuration using migrations/config tag.

## Git Requirements

- Create phase branch.
- Commit performance changes and reports.
- Tag phase completion.

## Review Package Requirements

- `docs/reviews/PHASE_12.1_CHANGESET.patch`
- `docs/reviews/PHASE_12.1_REVIEW_SUMMARY.md`

## Completion Criteria

- Performance goals are measured and met.
- No regression in correctness or security.
