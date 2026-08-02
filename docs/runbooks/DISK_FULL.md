# Disk Full

1. Confirm the affected filesystem and stop nonessential writes; do not delete database or backup files ad hoc.
2. Inspect container logs, media growth, PostgreSQL volume, n8n data, and backup retention.
3. Move verified backups to approved encrypted storage and rotate logs according to retention policy.
4. Expand capacity or remove only approved expired artifacts. Never use recursive cleanup against an unverified path.
5. Verify disk below 80 percent, database integrity, uploads, n8n, backup, and restore-test readiness.
