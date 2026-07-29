# Wave 4 Legacy Retirement Plan

## Retirement Position

Legacy is not removed in Wave 4. Retirement should be staged behind explicit review gates.

## Services Removable Later

Only after traffic/parity evidence and human approval:

- Legacy product write routes
- Legacy customer write routes
- Legacy quote/order workflow write routes
- Duplicate compatibility response helpers
- Legacy API routes replaced by `/api/v1/...`

## Services Requiring Compatibility

Keep until separate migration waves finish:

- Public page rendering in `backend/app.py`
- Admin CMS pages/forms
- Media manager/upload filesystem logic
- Runtime AI chatbot/translation/content tools
- System settings
- Queue and notifications
- Legacy read APIs needed by old frontend

## Not Retirable In Current State

- Payment processing
- Production routing
- Database files/backups
- Legacy auth/session data until session cutover is separately approved

## Shutdown Prerequisites

1. Route-level traffic evidence shows Django routes handle production traffic.
2. Legacy route count is zero for the target route group.
3. Backups are complete and restore tested.
4. Django API parity tests pass.
5. CMS/media/payment migration decisions are complete.
6. Human architecture approval is recorded.
7. Rollback route and runbook are ready.

## Rollback Plan

If a retired route fails:

1. Re-enable legacy route/proxy mapping.
2. Stop new Django writes for the affected module.
3. Preserve evidence and logs.
4. Compare Django payloads with legacy behavior.
5. Restore from backup only if data corruption is confirmed.

## Recommendation

Keep legacy system running in compatibility mode. Begin retirement only module by module after evidence-driven cutover review.
