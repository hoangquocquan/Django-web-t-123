# IIS Production Evidence Guide

## Purpose

Collect IIS production access logs and convert them into the standardized CSV
format used by Phase 11.1.5.4 production evidence validation.

## IIS Log Location

Default IIS log root:

```text
C:\inetpub\logs\LogFiles
```

Site-specific logs usually live in:

```text
C:\inetpub\logs\LogFiles\W3SVC<site-id>
```

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\detect_iis_site.ps1
```

The detector reports website name, site ID, physical path and expected log
location. It does not modify IIS.

## Enable Logging

In IIS Manager:

1. Select the website.
2. Open `Logging`.
3. Use W3C format.
4. Include at minimum: date, time, client IP, URI stem, HTTP status and user
   agent.

This project does not change IIS logging settings automatically.

## Export Logs

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\export_iis_api_evidence.ps1
```

Optional:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\export_iis_api_evidence.ps1 `
  -LogRoot "C:\inetpub\logs\LogFiles\W3SVC1" `
  -OutputPath "docs\migration\production_evidence\input\iis_api_evidence.csv"
```

## CSV Output

Output path:

```text
docs/migration/production_evidence/input/iis_api_evidence.csv
```

CSV columns:

```text
timestamp,source,client,endpoint,status_code,user_agent
```

## Verify CSV

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\validate_iis_api_evidence.ps1
```

Possible output:

```text
IIS_EVIDENCE_READY
IIS_EVIDENCE_INCOMPLETE
```

## Import Into Phase 11.1.5.4

Run:

```powershell
python scripts\phase11_1_5_4_production_evidence_loader.py --input docs\migration\production_evidence\input\iis_api_evidence.csv
```

Expected report:

```text
docs/migration/production_evidence/reports/REAL_PRODUCTION_TRAFFIC_REPORT.json
```

## Current Status

```text
IIS_EVIDENCE_INCOMPLETE
```

No real IIS production logs are included in this repository.
