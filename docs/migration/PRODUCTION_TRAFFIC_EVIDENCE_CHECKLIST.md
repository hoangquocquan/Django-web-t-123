# Production Traffic Evidence Checklist

## Purpose

Collect enough production evidence to decide whether legacy `/api/...` routes
can be decommissioned safely.

## Required Evidence

- [ ] Nginx access logs
- [ ] Load balancer logs
- [ ] API gateway logs
- [ ] Application access logs
- [ ] CDN logs, if applicable

## Verification Period

Recommended window:

```text
7-30 days
```

The window should include normal business days, weekend traffic if applicable,
scheduled jobs and partner integration runs.

## Traffic Checks

Legacy API:

```text
/api/*
```

Expected:

```text
0 requests
```

Django replacement API:

```text
/api/v1/*
```

Expected:

```text
active usage confirmed
```

## Evidence Command

```powershell
python scripts\phase11_1_4_production_traffic_evidence.py --log <production-log> --period <YYYY-MM-DD_to_YYYY-MM-DD>
```

Multiple logs:

```powershell
python scripts\phase11_1_4_production_traffic_evidence.py --log nginx.log --log gateway.jsonl --log application.csv
```

## Security Checklist

- [ ] Credentials masked
- [ ] Tokens removed
- [ ] Customer data redacted
- [ ] Logs treated read-only
- [ ] Raw logs not committed
- [ ] Only summary evidence is included in review package

## Current Status

```text
BLOCKED_SAFELY
```

No production logs are available in this repository, so legacy API remains
active.
