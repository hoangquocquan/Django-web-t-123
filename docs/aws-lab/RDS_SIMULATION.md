# RDS Simulation

## AWS Concept

Amazon RDS is a managed relational database service. It handles database
hosting, backups, updates, and monitoring.

## Local Equivalent

The lab uses a PostgreSQL container:

```text
AWS RDS PostgreSQL
-> postgres:16-alpine container
```

## Database Connection

Django connects with:

```text
DATABASE_URL=postgresql://mecprecision:mecprecision-local-password@postgres:5432/mecprecision_lab
```

## Backup Concept

RDS automated backups are simulated by mounting:

```text
docker/aws-lab/postgres/backups
```

Example local backup command:

```bash
docker exec mecprecision-aws-lab-postgres pg_dump -U mecprecision mecprecision_lab > backup.sql
```

## Migration Flow

1. Start PostgreSQL container.
2. Point Django `DATABASE_URL` to PostgreSQL.
3. Run Django migrations.
4. Validate application pages and APIs.
5. Practice backup and restore locally.

## Learning Outcome

You learn RDS concepts without creating an AWS database.
