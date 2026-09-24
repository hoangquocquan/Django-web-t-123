# S3 Simulation

## AWS Concept

Amazon S3 stores objects such as uploaded images, PDFs, static files, backups,
and generated reports.

## Local Equivalent

This lab uses MinIO:

```text
AWS S3
-> MinIO container
```

## MinIO Access

Console:

```text
http://localhost:9001/
```

Credentials:

```text
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=minio-local-password
```

## Django Configuration Concept

The compose file exposes S3-like settings:

- `AWS_LAB_S3_ENDPOINT_URL`
- `AWS_LAB_S3_BUCKET`
- `AWS_LAB_S3_ACCESS_KEY_ID`
- `AWS_LAB_S3_SECRET_ACCESS_KEY`

Current project state:

- Django still uses local `STATIC_ROOT`.
- Django still uses local `MEDIA_ROOT`.
- MinIO is present for learning and future storage integration.

## Static Files

Future production pattern:

```text
collectstatic -> S3 bucket -> CloudFront
```

## Media Files

Future production pattern:

```text
upload -> Django validation -> S3 bucket -> CDN/private URL policy
```

## Learning Outcome

You can learn S3 bucket concepts locally before wiring Django storage backend.
