# PROD-01 Known Limitations

- PostgreSQL, Redis, Docker daemon, and live n8n remain unverified. PROD-01 does
  not claim infrastructure readiness; those dependencies belong to later phases.
- The Lead Kanban intentionally displays the 25 most recently updated records in
  each status to keep response size bounded. Full search and pagination can be
  added as a later operational enhancement.
- The browser test uses a local ignored database account and Selenium cache; no
  credential or runtime database is staged.
- Raw mypy cannot model the inherited Django dynamic manager without
  `django-stubs`. Targeted application code passes after excluding that known
  environment limitation.
- User ZIP files remain untracked and untouched.
