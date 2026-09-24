# Production Client Dependency Report

## Purpose

Track every known client that may call legacy `/api/...` routes before shutdown.

## Current Decision

```text
KEEP_LEGACY_API_ACTIVE
```

Production client evidence is still missing. Local source dependency scan from
Phase 11.1.2 found documented replacements and no unknown local references, but
external clients still require production evidence.

## Client Dependency Matrix

| Client source | Client | Legacy API usage | Replacement API | Migration status |
|---|---|---|---|---|
| Frontend | Website browser UI | Locally documented legacy references | `/api/v1/public/home/`, `/api/v1/catalog/products/`, `/api/v1/crm/contact-requests/`, `/api/v1/sales/quotes/` | Needs production log confirmation |
| Mobile | Mobile app, if any | Not verified | `/api/v1/...` | Pending operator evidence |
| Integration | Partner integrations | Not verified | `/api/v1/...` | Pending operator evidence |
| Partner API | External partners | Not verified | `/api/v1/...` | Pending operator evidence |
| Scheduled jobs | Cron/background jobs | Not verified | `/api/v1/...` | Pending operator evidence |
| Internal scripts | Local automation/scripts | Local references mapped | `/api/v1/...` | Documented, needs production confirmation |

## Required Follow-up

1. Collect access logs for the approved 7-30 day period.
2. Identify every client marker or user-agent.
3. Confirm legacy `/api/...` count is zero.
4. Confirm replacement `/api/v1/...` traffic is active.
5. Update this report with real production evidence.

## Security Review

- Do not commit raw logs.
- Mask tokens and credentials.
- Redact customer names, emails and phone numbers from shared samples.
