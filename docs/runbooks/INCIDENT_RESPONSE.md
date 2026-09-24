# Incident Response

1. Record start time, affected service, alert, and correlation IDs; never copy secrets or customer content.
2. Check `/api/v1/health/`, protected operations health, Prometheus alerts, and structured logs.
3. Classify severity and assign a human incident owner. Freeze deployments for data integrity or security risk.
4. Apply the relevant outage or rollback runbook. AI may summarize evidence but cannot approve or execute protected actions.
5. Validate recovery, document the timeline/root cause, and obtain human closure approval.
