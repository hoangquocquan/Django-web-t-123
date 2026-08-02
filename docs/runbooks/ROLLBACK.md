# Release Rollback

1. Stop new deployment activity and identify the last approved image from the release manifest.
2. Capture current logs/metrics and create a backup before changing runtime state.
3. Obtain human approval, switch only the application image, and preserve PostgreSQL, Redis, media, and n8n volumes.
4. Run migrations only when the approved release procedure explicitly requires them; never reverse a destructive migration automatically.
5. Run health, authentication, business smoke, AI safety, and n8n HMAC checks before closing rollback.
