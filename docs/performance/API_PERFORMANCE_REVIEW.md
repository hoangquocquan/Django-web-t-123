# API Performance Review

## Scope

Phase 9.2 reviews read-only Django APIs before any database ownership migration.

## Query Count

Current tests cover bounded query counts for representative endpoints:

- catalog product list: count query plus joined page query
- CRM customer list: count query plus page query plus notes prefetch

Repositories remain responsible for `select_related` and `prefetch_related`.
API views must not call ORM directly.

## N+1 Query Review

Known protections:

- products use `select_related("category")`
- CRM customers use preloaded notes
- sales quotes use `select_related("customer")`
- quote detail loads items and files through repository methods
- CMS menu preloads child menu items

## Pagination Requirement

All list endpoints now support `limit` and `offset`.

Defaults:

- `limit`: 20
- `offset`: 0
- maximum `limit`: 100

Invalid pagination returns `400`.

## Large Dataset Handling

The API slices querysets before serialization. This avoids serializing full
tables for list endpoints and gives frontend clients a stable paging contract.

## Response Time Baseline

No production traffic baseline exists yet. Before production cutover, add:

- p50/p95/p99 response time tracking
- database query timing
- slow endpoint logging
- endpoint-level alerting

## Remaining Performance Risks

- Detail endpoints with large related collections may need page-level slicing in
  a future phase.
- Search/filtering is not yet implemented.
- No caching is enabled at the Django API layer.
