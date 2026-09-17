# Phase 6D PostgreSQL backup and restore drill

This procedure targets only the running `django-web-t-123-phase6-postgres`
container. It creates a custom-format dump under ignored
`.phase6/backup-restore/`, restores into a newly named temporary database in the
same Phase 6-owned PostgreSQL container, compares migration fingerprints, proves
the restored schema is readable, and drops the temporary database. It never
overwrites the source database or touches another Compose project.

With the Phase 6D stack healthy, run:

```powershell
pwsh -NoProfile -File scripts/phase6/Invoke-Phase6DBackupRestoreDrill.ps1
```

Success writes a sanitized `.phase6/backup-restore/latest-result.json`. The dump
can contain audit-sensitive fictional application data: keep it outside Git,
restrict access, encrypt it before off-host storage, define retention with the
Owner, and securely expire it according to that policy. Do not attach the dump
to a report.

For an actual recovery, stop writes, capture PostgreSQL and media at a consistent
checkpoint, restore to an isolated target first, verify migration/schema and a
bounded canonical read, then obtain Owner approval before changing routing. A
cache backup is not required: Redis is disposable and must be rebuilt after the
database is authoritative. Never restore over an unrelated or unclassified
database, and never use the drill script as a production restore tool.
