# Legacy API Final Shutdown Decision

## Current State

```text
KEEP_LEGACY_API_ACTIVE
```

Legacy `/api/...` routes remain active. Django `/api/v1/...` replacements are
available, but production shutdown approval is not complete.

## Evidence Summary

| Evidence | Status |
|---|---|
| API compatibility matrix | READY |
| Production traffic logs | NOT PROVIDED |
| Legacy `/api/...` count | NOT VERIFIED |
| Django `/api/v1/...` traffic | NOT VERIFIED |
| Unknown clients | NOT VERIFIED |
| Technical approval | PENDING |
| Business approval | PENDING |
| Rollback owner | PENDING |

## Risk Assessment

| Risk | Level | Reason |
|---|---|---|
| Unknown production clients still call legacy API | High | No production logs were provided |
| Rollback owner missing | High | Approval package is pending |
| Business impact unknown | Medium | User impact review is pending |
| Django replacement regression | Low | Automated tests pass locally |

## Rollback Plan

Use:

```text
docs/migration/LEGACY_API_DECOMMISSION_ROLLBACK.md
```

Rollback capability must remain available. Do not delete legacy API code or
remove route mappings before the rollback window closes.

## Approval Status

```text
technical_approval: pending
business_approval: pending
maintenance_window: pending
rollback_owner: pending
```

## Final Decision

```text
KEEP_LEGACY_API_ACTIVE
```

Reason:

Production evidence and final approvals are missing.
