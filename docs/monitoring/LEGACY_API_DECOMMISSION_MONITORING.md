# Legacy API Decommission Monitoring

## Purpose

Monitor whether disabling legacy `/api/...` routes is safe and reversible.

## Before Disable

Track:

- Legacy `/api/...` request count.
- Django `/api/v1/...` replacement request count.
- Unknown client count.
- 4xx and 5xx error rate.
- Latency for replacement endpoints.

## During Disable

Check every 5 minutes during the approved window:

| Metric | Expected |
|---|---|
| Legacy `/api/...` requests | 0 |
| Unknown clients | 0 |
| Django `/api/v1/...` requests | Active |
| 5xx errors | No spike |
| Contact/quote writes | Successful |

## After Disable

Continue monitoring for:

- Clients retrying old legacy endpoints.
- Broken frontend calls.
- Failed quote or contact submissions.
- Authentication/session errors.
- Increased API latency.

## Alert Actions

If an alert triggers:

1. Pause further decommission steps.
2. Run the rollback guide.
3. Preserve logs.
4. Document client identity and affected endpoint.
5. Create a corrective minor phase.
