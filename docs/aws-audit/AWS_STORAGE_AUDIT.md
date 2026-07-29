# AWS Storage Audit

## Current Status

No real S3 bucket configuration or IAM storage policy was found.

Evidence found:

- Django uses local `MEDIA_ROOT = django_backend/media`.
- Docker Compose maps `media-data` volume to `/app/django_backend/media`.
- Existing migration docs mention future S3/CDN readiness.
- Nginx sample proxies `/uploads/` to the app.

## Static Files

Current static handling is local Django/staticfiles oriented.

Production needs:

- `collectstatic` workflow.
- S3 or container-hosted static strategy.
- CloudFront cache policy.

## Media Files

Current media/upload strategy is local filesystem or Docker volume.

Production needs:

- S3 bucket for media uploads.
- Private/public object policy decision.
- Lifecycle rules.
- Malware scanning policy if customer files are accepted.

## Backup Storage

No S3 backup bucket evidence was found.

## Recommendation

Use:

- S3 bucket for media.
- S3 or image artifact for static files.
- CloudFront for public static/media distribution.
- Separate backup bucket with lifecycle retention and access logging.
