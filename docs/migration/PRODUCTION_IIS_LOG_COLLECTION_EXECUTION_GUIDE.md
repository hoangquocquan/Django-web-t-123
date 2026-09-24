# Production IIS Log Collection Execution Guide

## Purpose

This guide explains how an operator collects real IIS production logs and
generates the evidence package required before Legacy API shutdown can be
reviewed.

This guide is read-only. It does not authorize shutdown, route changes, IIS
configuration changes, proxy changes, database changes or production code
changes.

## Server Access

Required access:

- Windows Server access.
- Administrator PowerShell, or an account with read permission to IIS logs.
- Permission to copy reviewed log evidence into the project evidence folder.

Do not restart IIS, recycle application pools or change IIS settings during this
collection.

## Identify IIS Site

Run the read-only site detector:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\detect_iis_site.ps1
```

Record:

- IIS website name.
- IIS Site ID.
- Physical path.
- Log folder.

The IIS log folder usually follows this pattern:

```text
C:\inetpub\logs\LogFiles\W3SVC<SITE_ID>
```

Example:

```text
C:\inetpub\logs\LogFiles\W3SVC1
```

## Log Collection

Collect IIS W3C log files:

```text
u_ex*.log
```

Required period:

- Minimum: `7 days`
- Recommended: `30 days`

Copy reviewed logs into:

```text
docs/migration/production_evidence/input/iis_logs/
```

## Export API Evidence CSV

Run the wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\run_production_iis_evidence_collection.ps1 `
  -LogRoot "C:\inetpub\logs\LogFiles\W3SVC<SITE_ID>" `
  -CollectionPeriod "2026-07-01 to 2026-07-30"
```

The wrapper runs:

- `detect_iis_site.ps1`
- `diagnose_iis_evidence.ps1`
- `export_iis_api_evidence.ps1`
- `phase11_1_6_5_1_collection_validator.py`

Expected CSV output:

```text
docs/migration/production_evidence/input/iis_api_evidence.csv
```

Expected columns:

```text
timestamp,source,client,endpoint,status_code,user_agent
```

## Security

Before upload or commit, review evidence and remove sensitive data:

- passwords
- tokens
- cookies
- authorization headers
- session identifiers
- private customer data not needed for traffic validation

Prefer sanitized CSV/report artifacts for Git review. Store raw logs outside Git
if they contain sensitive production information.

## Validation

Run:

```powershell
python scripts\phase11_1_6_5_1_collection_validator.py `
  --period "2026-07-01 to 2026-07-30"
```

The result is complete only when:

- IIS logs exist.
- CSV export exists.
- CSV rows are greater than `0`.
- Collection period exists.
- Legacy `/api/*` traffic is `0`.
- Django `/api/v1/*` traffic is greater than `0`.
- Unknown clients are `0`.

## Output Package

Evidence package:

```text
docs/migration/production_evidence/
├── input/
│   ├── iis_logs/
│   └── iis_api_evidence.csv
└── reports/
    └── REAL_PRODUCTION_EVIDENCE_REPORT.json
```

Review report:

```text
docs/reviews/PHASE_11.1.6.5.1_COLLECTION_RESULT.md
```

## Stop Conditions

Keep Legacy API active and stop the shutdown path when:

- IIS logs are missing.
- CSV export is empty.
- Collection period is missing.
- Legacy `/api/*` traffic is still detected.
- Replacement `/api/v1/*` traffic is not confirmed.
- Unknown clients are detected.

## Final Reminder

This phase prepares evidence only. It does not execute shutdown and does not
start Phase 11.2.
