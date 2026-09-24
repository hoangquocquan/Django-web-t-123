# n8n Outage

1. Confirm n8n health, PostgreSQL availability, and the n8n data volume.
2. Disable incoming workflow triggers at the trusted proxy only with human approval; do not run queued business actions manually.
3. Restore n8n with the same encryption key, database, and versioned workflows.
4. Validate webhook HMAC rejection and the human-approval gate before reopening traffic.
5. Reconcile workflow executions by correlation ID; never replay an action blindly.
