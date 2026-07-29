# Wave 4 Payment Ownership Decision

## Decision

```text
REQUIRE_FUTURE_PROJECT
```

## Reason

No approved Django payment architecture exists in the current migration waves. The repository does not show a complete, validated external payment integration ready for direct Django ownership.

Payment affects money movement, customer trust, compliance, audit logs, refunds, reconciliation, and incident response. It must not be migrated as a side effect of legacy reduction.

## Risk

| Risk | Level | Note |
|---|---|---|
| Incorrect charge/refund behavior | High | Requires provider sandbox and reconciliation tests |
| Secret exposure | High | Needs environment/secrets hardening |
| Incomplete audit trail | High | Must align with transaction history and accounting needs |
| Rollback complexity | High | Payment state cannot always be rolled back like normal database writes |
| Compliance ambiguity | High | Requires explicit business and legal/security review |

## Recommendation

Create a dedicated payment migration project after Django API ownership is approved.

Minimum prerequisites:

- Payment provider selection and sandbox
- Secrets management design
- Payment state machine
- Webhook signature verification
- Refund/reconciliation workflow
- End-to-end integration tests
- Human approval gate
- Production rollback plan

## Boundary

Wave 4 does not migrate payment, does not modify payment routes, and does not approve production payment cutover.
