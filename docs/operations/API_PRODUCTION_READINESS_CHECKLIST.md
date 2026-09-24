# API Production Readiness Checklist

## Architecture

- [x] API routes are centralized in `apps.api`.
- [x] API views call services only.
- [x] Services call repositories.
- [x] Repositories own ORM access.
- [x] Legacy database remains read-only.

## Security

- [x] Unsafe methods are blocked.
- [x] Sensitive auth fields are not exposed.
- [x] Login cutover is not implemented accidentally.
- [ ] Real production authentication approved.
- [ ] Rate limiting approved.

## Performance

- [x] List endpoints support pagination.
- [x] Representative query count tests exist.
- [x] API views avoid direct ORM access.
- [ ] Production latency baseline collected.
- [ ] Caching strategy approved if needed.

## Testing

- [x] `python manage.py check`
- [x] API endpoint tests
- [x] permission tests
- [x] response schema tests
- [x] invalid request tests
- [x] full regression tests

## Monitoring

- [x] Monitoring plan documented.
- [ ] Request logging implementation approved.
- [ ] Metrics collection approved.
- [ ] Alert thresholds approved.

## Rollback

- [x] Health rollback plan exists.
- [x] API cutover strategy exists.
- [ ] Production route rollback tested with real proxy/router.

## Documentation

- [x] API reference
- [x] API versioning strategy
- [x] OpenAPI readiness document
- [x] Performance review
- [x] Security hardening document
- [x] Monitoring plan
