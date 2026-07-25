# Legacy API Traffic Audit

## Phase

Phase 11.1.2 - Legacy API Traffic Verification

## Current Context

Phase 11.1.1 completed Django replacements for 15/15 known legacy API route
groups. The remaining blocker is production traffic evidence.

## Traffic Sources

| Source | Legacy API usage | Replacement API | Status |
|---|---|---|---|
| Public frontend pages | Potential historical `/api/...` calls | `/api/v1/...` | Needs source scan |
| Admin/CMS frontend | Potential product/contact/quote calls | `/api/v1/catalog`, `/api/v1/crm`, `/api/v1/sales` | Needs source scan |
| Mobile clients | Unknown | `/api/v1/...` | Production access logs required |
| External integrations | Unknown | `/api/v1/...` | Integration logs required |
| Scheduled jobs/scripts | Potential script references | `/api/v1/...` | Source scan required |
| Internal developer tools | Potential legacy test references | `/api/v1/...` | Source scan required |

## Required Evidence

- API gateway/proxy logs for the verification period.
- Legacy backend access logs if still running.
- Django API access logs proving `/api/v1/...` usage.
- Client/integration inventory from operators.
- Confirmation that logs have secrets masked before review.

## Current Decision

```text
KEEP_LEGACY_API_ACTIVE
```

This phase provides verification tooling. It does not claim production traffic
is zero unless production log files are supplied and pass the verification
script.
