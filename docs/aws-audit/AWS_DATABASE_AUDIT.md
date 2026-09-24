# AWS Database Audit

## Current Status

No AWS RDS configuration or live database inventory was found.

Evidence found:

- Django `DATABASE_URL` supports SQLite and PostgreSQL parsing.
- `docker-compose.yml` includes a local `postgres:16-alpine` service.
- `Dockerfile` defaults to SQLite inside the container.
- Legacy SQLite remains at `backend/database/mecprecision.sqlite`.
- Prior migration phases prepared Django-owned models and PostgreSQL dry-run documentation.

## Database Ownership

Django now owns multiple migrated domains, but production database ownership is not fully cut over to AWS RDS in this repository.

## Django Compatibility

Django is compatible with PostgreSQL via `DATABASE_URL`.

Required production configuration:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME
```

## Risk Assessment

| Risk | Severity | Notes |
| --- | --- | --- |
| SQLite in production | High | Not suitable for scalable AWS deployment |
| No RDS backup evidence | High | Backup/restore controls not proven |
| Legacy read database still present | Medium | Requires final ownership review |
| Secrets in plain env | Medium | Use AWS Secrets Manager or SSM Parameter Store |

## Recommendation

Use RDS PostgreSQL with automated backups, point-in-time recovery, private subnets, restricted security groups, and migration rehearsal before cutover.
