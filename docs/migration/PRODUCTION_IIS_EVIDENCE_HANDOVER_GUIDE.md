# Production IIS Evidence Handover Guide

## Purpose

Real production evidence is required before Legacy API shutdown because the
team must prove that production clients are already using the Django replacement
API and no important client still depends on the old `/api/*` route.

This handover package helps the Windows Server IIS administrator collect,
sanitize and deliver that evidence without changing production behavior.

## Required Access

The operator needs:

- Windows Server access.
- IIS Manager access.
- Read permission to `C:\inetpub\logs\LogFiles`.
- Permission to run read-only PowerShell scripts.
- Permission to copy reviewed evidence files into the project evidence folder.

Do not restart IIS, recycle app pools, change bindings, change rewrite rules or
edit IIS logging settings as part of this handover.

## Collection Period

Minimum:

`7 days`

Recommended:

`30 days`

The collection period must be written into:

`docs/migration/production_evidence/handover/collection_metadata.json`

## Files Required

Collect IIS W3C log files:

```text
u_ex*.log
```

Place reviewed copies in:

```text
docs/migration/production_evidence/input/iis_logs/
```

Generate the CSV export:

```text
docs/migration/production_evidence/input/iis_api_evidence.csv
```

## Required IIS Fields

Every accepted IIS W3C log must include:

- `date`
- `time`
- `c-ip`
- `cs-uri-stem`
- `sc-status`
- `cs(User-Agent)`

Recommended fields:

- `cs-method`
- `cs-uri-query`
- `s-ip`
- `s-port`

## Collection Command

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\run_production_iis_evidence_collection.ps1 `
  -LogRoot "C:\inetpub\logs\LogFiles\W3SVC<SITE_ID>" `
  -CollectionPeriod "YYYY-MM-DD to YYYY-MM-DD"
```

## Delivery Command

After evidence is copied into the package, run:

```powershell
python scripts\phase11_1_6_5_2_evidence_acceptance_validator.py
```

Expected after valid evidence:

```text
EVIDENCE_ACCEPTED
```

If the result is:

```text
EVIDENCE_REJECTED
```

do not continue to shutdown review. Fix the missing evidence and rerun the
validator.

## Security Review

Before delivery, remove or mask:

- passwords
- tokens
- cookies
- authorization headers
- session identifiers
- sensitive customer data not needed for traffic validation

Raw IIS logs may include client IPs and user agents. If policy does not allow
committing raw logs, store raw logs outside Git and provide an approved,
sanitized CSV plus metadata for review.

## Safety Confirmation

This handover does not authorize:

- Legacy API shutdown
- IIS route changes
- proxy changes
- database changes
- production code changes
