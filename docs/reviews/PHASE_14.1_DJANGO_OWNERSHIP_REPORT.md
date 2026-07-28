# Phase 14.1 Django Ownership Report

## Selected Domain

```text
Newsletter subscribers
```

## Before Architecture

Legacy owned newsletter writes. Django only had a CMS read-only unmanaged mapping to the legacy `newsletter_subscribers` table.

## After Architecture

Django now owns newsletter writes through:

- `apps.newsletter.models.NewsletterSubscriber`
- `apps.newsletter.services.NewsletterService`
- `/api/v1/newsletter/subscribers/`

Legacy CMS compatibility remains through:

- `apps.cms.models.NewsletterSubscriber`
- `apps.cms.repositories.newsletter_repository.NewsletterRepository`

## Database Ownership Change

The selected domain now has a managed Django model and Django migration files.

Migration files:

- `newsletter.0001_initial`
- `newsletter.0002_import_legacy_subscribers`

## API Migration

New endpoint:

```text
GET /api/v1/newsletter/subscribers/
POST /api/v1/newsletter/subscribers/
```

Behavior:

- `GET` lists Django-owned subscribers.
- `POST` creates or reactivates a subscriber using serializer validation.
- Duplicate email requests are idempotent and return the existing subscriber.

## Test Result

```text
pytest tests/test_phase14_1_django_ownership.py
8 passed

python manage.py makemigrations --check --dry-run
No changes detected

pytest
188 passed
```

## AI Review

```text
PASS
```

AI Factory:

```text
AI_SOFTWARE_FACTORY_COMPLETE
```

Factory final decision:

```text
WAITING_FOR_HUMAN_APPROVAL
```

## Remaining Legacy Dependency

- Legacy backend remains in place.
- Legacy CMS newsletter read-only repository remains for compatibility.
- Other domains are not migrated in this phase.

## Final Status

```text
DJANGO_OWNERSHIP_MIGRATION_COMPLETE
```
