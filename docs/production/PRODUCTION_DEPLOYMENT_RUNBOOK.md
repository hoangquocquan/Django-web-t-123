# Production deployment runbook

Status: `MANUAL_EXECUTION_REQUIRED`. This repository does not deploy production.

1. Freeze the reviewed commit SHA and change scope.
2. Build the immutable backend artifact in CI.
3. Build the immutable frontend artifact from the same SHA.
4. Record both artifact/image digests; do not rely on `latest`.
5. Verify required CI belongs to the exact frozen SHA.
6. Obtain two-person go/no-go approval and name the rollback owner.
7. Inject secrets from the external secret manager, never a repository `.env` file.
8. Run `python scripts/production_preflight.py`; retain only sanitized output.
9. Verify database, TLS, Redis, durable media and enabled provider connectivity from staging.
10. Create and verify the approved database/media backup.
11. Run `manage.py migrate --plan` and review risk, compatibility and lock budget.
12. Confirm the maintenance window and readiness decision.
13. Deploy the backend artifact to a canary using its digest.
14. Run reviewed migrations exactly once from the designated release job.
15. Run `manage.py migrate --check` and `manage.py check --deploy`.
16. Deploy the frontend artifact identified by the matching SHA/digest.
17. Verify liveness/readiness and `python scripts/production_read_only_smoke.py --base-url https://<host>`.
18. Observe error rate, latency, readiness, database saturation and queues for the approved window.
19. Record the human go/no-go decision before full promotion.
20. Roll back to the prior known-good digest or initiate reviewed forward recovery on any failed gate.

Stop and roll back on any failed gate. Do not enable `LINE_SEND_ENABLED`; LINE activation is a separate approved change. Record approvers, UTC times, commit, digest, migration-plan hash, backup ID, smoke results and dashboards without secrets.

For `DATABASE_SSLMODE=verify-full`, mount the managed database CA bundle read-only, configure the PostgreSQL root-certificate path, and verify hostname/SAN matching. `require` encrypts transport but does not authenticate the server and needs an explicit risk acceptance.
