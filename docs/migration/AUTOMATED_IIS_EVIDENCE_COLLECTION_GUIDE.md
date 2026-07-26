# Automated IIS Evidence Collection Guide

## Purpose

`Collect-IIS-Production-Evidence.ps1` is a one-click evidence collection tool
for Windows Server administrators. It collects IIS W3C logs, exports API traffic
to CSV, generates handover metadata and runs the evidence acceptance validator.

The tool is evidence-only. It does not shutdown Legacy API, disable routes,
modify IIS configuration, modify proxy settings or modify databases.

## Installation

Copy the project folder or these files to the Windows Server:

```text
scripts/windows/Collect-IIS-Production-Evidence.ps1
scripts/windows/export_iis_api_evidence.ps1
scripts/phase11_1_6_5_2_evidence_acceptance_validator.py
scripts/phase11_1_6_2_real_production_evidence.py
docs/migration/production_evidence/
```

Run PowerShell from the project root.

## Requirements

- Windows Server.
- IIS installed.
- IIS W3C logging enabled.
- Read permission to `C:\inetpub\logs\LogFiles`.
- PowerShell execution permission for local scripts.
- Python available as `python`.

Required IIS W3C fields:

- `date`
- `time`
- `c-ip`
- `cs-uri-stem`
- `sc-status`
- `cs(User-Agent)`

## Running Script

Default collection window, last 7 days:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\Collect-IIS-Production-Evidence.ps1 `
  -Reviewer "Architecture Reviewer"
```

Recommended collection window, last 30 days:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\Collect-IIS-Production-Evidence.ps1 `
  -Days 30 `
  -Reviewer "Architecture Reviewer"
```

Specific IIS site:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\Collect-IIS-Production-Evidence.ps1 `
  -SiteId 1 `
  -Days 30 `
  -Reviewer "Architecture Reviewer"
```

Specific log folder:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\Collect-IIS-Production-Evidence.ps1 `
  -LogRoot "C:\inetpub\logs\LogFiles\W3SVC1" `
  -Days 30 `
  -Reviewer "Architecture Reviewer"
```

## Output Files

Evidence package:

```text
docs/migration/production_evidence/
├── input/
│   ├── iis_logs/
│   │   └── u_ex*.log
│   └── iis_api_evidence.csv
├── reports/
└── handover/
    ├── collection_metadata.json
    └── EVIDENCE_ACCEPTANCE_STATUS.json
```

Acceptance review:

```text
docs/reviews/PHASE_11.1.6.5.2_EVIDENCE_HANDOVER_REVIEW.md
```

## Successful Result

When valid production logs exist and all validation checks pass, the script
returns:

```text
COMPLETE_EVIDENCE_PACKAGE
```

The acceptance validator returns:

```text
EVIDENCE_ACCEPTED
```

## Troubleshooting

### IIS not installed

The script returns `IIS_NOT_DETECTED`. Run it on the Windows Server that hosts
IIS or provide the correct evidence package manually.

### IIS websites not detected

Confirm the `WebAdministration` module is available and the account has
permission to read IIS website information.

### IIS logs missing

Confirm the selected site ID and log folder:

```text
C:\inetpub\logs\LogFiles\W3SVC<SITE_ID>
```

### CSV is empty

Possible reasons:

- No `/api/*` or `/api/v1/*` traffic happened during the selected window.
- Wrong IIS site/log folder was selected.
- API traffic is handled by another proxy, load balancer, CDN or API gateway.
- IIS log fields do not include `cs-uri-stem`.

### Evidence rejected

Open:

```text
docs/migration/production_evidence/handover/EVIDENCE_ACCEPTANCE_STATUS.json
```

Fix the listed errors and rerun the tool.

## Safety Notes

Before sharing evidence, remove or mask passwords, tokens, cookies,
authorization headers and sensitive customer data. Store raw logs outside Git if
security policy requires it.
