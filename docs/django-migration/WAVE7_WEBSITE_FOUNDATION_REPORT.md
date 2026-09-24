# Wave 7 Website Foundation Report

## Django App

Created:

`django_backend/apps/website/`

Main files:

- `forms.py`
- `views.py`
- `urls.py`
- `templates/website/`
- `static/website/site.css`

## URL Ownership

Django now owns:

- `/`
- `/products`
- `/product/<slug>`
- `/technology`
- `/news`
- `/news/<slug>`
- `/contact`

## Layout

The base template includes:

- header
- navigation
- footer
- SEO title
- SEO description
- canonical URL
- static CSS

## Data Sources

- Product pages use `BusinessProduct`.
- Technology capability content uses `CatalogService` with fallback content.
- News content uses `CmsService` read path.
- Contact and quote forms use `replacement_submission_service.create_submission()`.

## Security

- CSRF middleware remains enabled.
- Contact and quote forms include CSRF token.
- Forms validate required fields and captcha.
- No secrets are rendered in public templates.
