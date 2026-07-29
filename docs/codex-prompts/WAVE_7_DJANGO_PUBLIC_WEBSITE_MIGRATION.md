# Wave 7 - Django Public Website Migration

## Objective

Move public website rendering from the legacy frontend/backend into Django while preserving SEO URLs and rollback compatibility.

## Scope

- Public website app.
- Homepage.
- Product listing and product detail.
- Technology page.
- News listing and news detail.
- Contact and quote request forms.
- SEO metadata and static assets.

## DO NOT

- Do not delete the legacy website.
- Do not break existing SEO URLs.
- Do not migrate external systems.
- Do not remove old assets without replacement.
- Do not rewrite unrelated backend logic.

## Implementation Tasks

1. Audit legacy public routes and dependencies.
2. Create `apps.website` foundation.
3. Render `/` homepage from Django.
4. Render `/products` and `/product/<slug>`.
5. Render `/technology`.
6. Render `/news`, `/news/<slug>`, and `/contact`.
7. Store contact/quote submissions through safe Django submission intent service.
8. Add tests and AI Factory evidence.

## Testing Requirements

- `python manage.py check`
- `pytest tests/test_wave7_public_website.py`
- `pytest`
- `python ai-factory/run_ai_factory.py --wave django-wave-7`

## Git Requirements

- Branch: `feature/wave-7-django-public-website-migration`
- Commit: `feat: migrate public website ownership to django`
- Tag: `wave-7-public-website-complete`

## Expected Output

Final status: `DJANGO_PUBLIC_WEBSITE_MIGRATION_COMPLETE`.
