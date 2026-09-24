# PROD-04 Live n8n Orchestration

The `n8n` Compose service stores workflow state in PostgreSQL and credentials in its persistent volume using `N8N_ENCRYPTION_KEY`.

## Workflows

- `prod04_ai_runtime_gate.json`: authenticated webhook, safety-gate validation, bounded Django health retry, correlation ID, and approval-pending response.
- `prod04_error_workflow.json`: local fail-closed error record without external notification or protected action.

## Required Environment

Set `N8N_ENCRYPTION_KEY` and `N8N_WEBHOOK_SECRET` outside Git. Start the production-like Compose stack, import both workflows with the n8n CLI, publish the main workflow, then call `/webhook/prod04-runtime-review` with an HMAC-SHA256 `X-MEC-Signature`.

The signed JSON must contain the four safety gates. Invalid signatures, missing correlation IDs, malformed gates, auto-merge, auto-deploy, or approval bypass all fail closed.

## Operational Boundary

n8n checks runtime health only. It cannot merge code, deploy, approve its own work, write business records, or advance a production phase. A human remains the final approval authority.
