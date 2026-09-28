# Rollback runbook

Declare an incident, freeze promotion and identify the last known-good digest. Roll back application only when schema is backward-compatible. For irreversible migrations use the reviewed forward-recovery plan, never an improvised destructive reversal. Disable outbound integrations, deploy the known-good digest, run read-only smoke, monitor recovery and record evidence. Database restore requires separate approval.
