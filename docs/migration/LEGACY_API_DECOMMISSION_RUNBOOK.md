# Legacy API Decommission Runbook

## Current Status

```text
NOT APPROVED FOR EXECUTION
```

This runbook must not be executed until production traffic evidence proves that
legacy API routes are unused.

## Readiness Command

```powershell
python scripts\phase11_1_legacy_api_decommission_readiness.py
```

Strict mode for CI:

```powershell
python scripts\phase11_1_legacy_api_decommission_readiness.py --strict
```

## Required Evidence

| Evidence | Required marker |
|---|---|
| Django API production contracts verified | `PHASE11_1_DJANGO_API_CONTRACTS_VERIFIED=verified` |
| Zero legacy API traffic confirmed | `PHASE11_1_ZERO_LEGACY_API_TRAFFIC_CONFIRMED=verified` |
| Client contract tests passed | `PHASE11_1_CLIENT_CONTRACT_TESTS_PASSED=passed` |
| Rollback window respected | `PHASE11_1_ROLLBACK_WINDOW_RESPECTED=approved` |
| Access logs archived | `PHASE11_1_ACCESS_LOGS_ARCHIVED=verified` |
| Approval ID | `PHASE11_1_DECOMMISSION_APPROVAL_ID=<approval-id>` |

## Manual Decommission Sequence After Approval

1. Export and archive legacy API access logs.
2. Confirm no `/api/` legacy requests appear in the approved log window.
3. Confirm Django replacement endpoints pass contract tests.
4. Confirm clients have switched to `/api/v1/...`.
5. Add redirect/proxy rules only if approved by architecture review.
6. Disable legacy API routes gradually by risk group.
7. Keep rollback mapping available until the rollback window closes.
8. Monitor error rate and client traffic after each change.

## Stop Conditions

Stop immediately if:

- Any client still calls a legacy `/api/` endpoint.
- Any endpoint lacks a Django replacement or approved removal decision.
- Django API regression fails.
- Rollback owner rejects the cutover window.

## Rollback

Rollback means restoring the previous route/proxy mapping so client requests go
back to the legacy backend. Do not delete legacy API code before the rollback
window closes.
