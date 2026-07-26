# IIS Production Evidence Deployment Guide

## 1. Purpose

Phase 11.1.5.5 collects IIS production evidence before legacy API shutdown. The
goal is to read IIS W3C access logs, export only API traffic evidence to CSV and
feed that CSV into the Phase 11.1.5.4 production evidence loader.

This process is read-only. It must not modify IIS configuration, restart IIS,
change routing, disable legacy API routes or alter production traffic.

## 2. Requirements

Environment:

- Windows Server
- IIS
- Administrator PowerShell
- Access to IIS W3C log files
- Project files copied to or accessible from the server

Repository scripts:

```text
scripts/windows/detect_iis_site.ps1
scripts/windows/export_iis_api_evidence.ps1
scripts/windows/validate_iis_api_evidence.ps1
```

## 3. IIS Site Detection

IIS site information is normally available through:

```powershell
Get-Website
```

Run the safe detector:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\detect_iis_site.ps1
```

Use the output to identify:

- Website name
- Site ID
- Physical path
- W3SVC log folder

The W3SVC folder usually follows this pattern:

```text
C:\inetpub\logs\LogFiles\W3SVC<site-id>
```

Example:

```text
Site ID: 1
Log folder: C:\inetpub\logs\LogFiles\W3SVC1
```

## 4. IIS Logging Verification

Open IIS Manager:

1. Select the target website.
2. Open `Logging`.
3. Confirm log format is `W3C`.
4. Confirm the log directory.
5. Confirm required W3C fields are enabled.

Required W3C fields:

```text
date
time
c-ip
cs-uri-stem
sc-status
cs(User-Agent)
```

Recommended extra fields:

```text
cs-method
cs-uri-query
s-ip
s-port
cs-username
```

If any required field is missing, collect a corrected log window before using
the output for shutdown approval.

## 5. Script Deployment

Copy or keep these files on the server:

```text
scripts/windows/
├── detect_iis_site.ps1
├── export_iis_api_evidence.ps1
└── validate_iis_api_evidence.ps1
```

The scripts only read IIS logs and write local evidence CSV/report output. They
do not call `Set-Website`, `Stop-Website`, `Restart-WebAppPool`, route changes
or IIS configuration commands.

## 6. Evidence Export Workflow

```text
IIS Logs
↓
PowerShell Collector
↓
docs/migration/production_evidence/input/iis_api_evidence.csv
↓
Phase 11.1.5.4 Loader
↓
docs/migration/production_evidence/reports/REAL_PRODUCTION_TRAFFIC_REPORT.json
```

Export command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\export_iis_api_evidence.ps1 `
  -LogRoot "C:\inetpub\logs\LogFiles\W3SVC1" `
  -OutputPath "docs\migration\production_evidence\input\iis_api_evidence.csv"
```

## 7. CSV Format

Output file:

```text
docs/migration/production_evidence/input/iis_api_evidence.csv
```

CSV columns:

```text
timestamp,source,client,endpoint,status_code,user_agent
```

Column meaning:

| Column | Description |
|---|---|
| `timestamp` | Combined IIS `date` and `time` |
| `source` | IIS log file path |
| `client` | IIS `c-ip` value |
| `endpoint` | IIS `cs-uri-stem` |
| `status_code` | IIS `sc-status` |
| `user_agent` | IIS `cs(User-Agent)` |

## 8. Validation Procedure

Detect IIS site:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\detect_iis_site.ps1
```

Export IIS evidence:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\export_iis_api_evidence.ps1
```

Validate exported CSV:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\validate_iis_api_evidence.ps1
```

Import into Phase 11.1.5.4:

```powershell
python scripts\phase11_1_5_4_production_evidence_loader.py --input docs\migration\production_evidence\input\iis_api_evidence.csv
```

Expected results before shutdown can proceed:

```text
validate_iis_api_evidence.ps1: IIS_EVIDENCE_READY
phase11_1_5_4_production_evidence_loader.py: COMPLETE_EVIDENCE_PACKAGE
```

## 9. Troubleshooting

### No IIS logs found

Check:

- IIS logging is enabled.
- You selected the correct website.
- The `-LogRoot` path points to the correct `W3SVC<site-id>` folder.
- The PowerShell user can read the log directory.

### Wrong W3SVC folder

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\detect_iis_site.ps1
```

Match the site ID to the correct `W3SVC<site-id>` folder.

### Empty CSV

Possible reasons:

- No `/api/*` traffic happened during the selected log window.
- The wrong log folder was used.
- IIS logging fields do not include `cs-uri-stem`.
- API traffic is handled by another server, reverse proxy or application layer.

### No /api traffic

Confirm whether the website actually receives API traffic. Some deployments may
serve API traffic through another host, load balancer, proxy, API gateway or
Django service outside IIS.

### API hosted outside IIS

Use the appropriate source instead:

- Load balancer logs
- API gateway logs
- Django/application logs
- CDN logs

Then feed the export into:

```powershell
python scripts\phase11_1_5_4_production_evidence_loader.py --input <export-file>
```

## 10. Security

Evidence collection must protect production data.

Rules:

- Do not export credentials or secret headers.
- Mask tokens in any shared samples.
- Protect customer IPs and user-agent data as operational evidence.
- Store raw logs outside Git.
- Commit only summarized CSV/report artifacts approved for review.
- Keep scripts read-only against IIS and production traffic.

## Phase Readiness

Current repository status:

```text
IIS_EVIDENCE_INCOMPLETE
KEEP_LEGACY_API_ACTIVE
```

Production execution is ready as a documented workflow, but shutdown approval
still requires real IIS evidence and successful Phase 11.1.5.4 validation.
