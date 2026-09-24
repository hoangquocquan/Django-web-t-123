# Phase 14.1 Domain Selection

## Selected Domain

```text
Newsletter subscribers
```

## Reason

Newsletter subscribers are the safest first Django ownership target because:

- The table is small.
- The business logic is simple.
- The domain has low dependency on products, quotes, auth, or CMS page rendering.
- Existing Django CMS read-only mapping already proves the legacy schema is understood.
- A write API can be tested without affecting core sales or catalog flows.

## Legacy Location

Legacy source files:

- `backend/services/cms_service.py`
- `backend/repositories/cms_repository.py`
- `backend/database/mecprecision.sqlite`
- `newsletter_subscribers` table

Existing Django read-only compatibility:

- `django_backend/apps/cms/models.py`
- `django_backend/apps/cms/repositories/newsletter_repository.py`
- `django_backend/apps/cms/services/cms_service.py`

## Django Target Location

New Django-owned domain:

- `django_backend/apps/newsletter/`

New API target:

- `/api/v1/newsletter/subscribers/`

## Migration Risks

| Risk | Level | Mitigation |
| --- | --- | --- |
| Duplicate email during data import | Low | Unique email constraint and idempotent data import |
| Breaking CMS read-only tests | Low | Keep existing CMS legacy model and repository unchanged |
| Confusing legacy vs Django-owned subscriber sources | Medium | Document ownership boundary and use a separate `apps.newsletter` app |
| Future unsubscribe workflow not complete | Low | Keep Phase 14.1 limited to subscribe/list/get ownership |

## Decision

Proceed with newsletter subscribers as the first Django-owned domain.
