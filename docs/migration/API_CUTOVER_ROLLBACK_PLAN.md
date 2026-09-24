# API Cutover Rollback Plan

## Endpoint

```http
GET /api/health
```

## Rollback Trigger

Rollback if any of these checks fail:

- contract tests detect a response shape mismatch
- health endpoint returns unexpected non-200 status
- proxy or frontend route cannot reach Django reliably
- monitoring shows degraded behavior after cutover

## Rollback Steps

1. Remove or disable the Django route/proxy rule for `/api/health`.
2. Route `/api/health` back to the legacy backend.
3. Run legacy health smoke test.
4. Run Django contract tests to confirm the issue is isolated.
5. Document the rollback reason in the phase review notes.

## Safety

This rollback is safe because Phase 9 health cutover:

- does not write database data
- does not change legacy code
- does not migrate schema
- does not affect authentication/session handling

## Smoke Endpoint

Django exposes a read-only rollback status endpoint:

```http
GET /api/v1/cutover/health/rollback/
```

This endpoint only explains the rollback plan. It does not mutate runtime
configuration.
