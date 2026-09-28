# LINE and n8n production boundary

`LINE_SEND_ENABLED` defaults to and remains false during general deployment. n8n never calls LINE directly; approved sends pass through Django after exact-content human approval, allowlist, environment, hash and idempotency checks. UAT credentials/recipients are not production credentials. Workflow activation and production sending require a separate reviewed release. This remediation sends no LINE message and activates no workflow.
