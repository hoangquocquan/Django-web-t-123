# IIS Production Evidence Operator Runbook

## Purpose

This runbook guides an operator through collecting IIS production evidence for
Legacy API shutdown readiness. It is read-only and evidence-only.

## Step 1: Connect To Windows Server

1. Connect to the production Windows Server using the approved access method.
2. Open PowerShell with the required read permissions.
3. Confirm the project scripts are available on the server or copied to a safe
   working directory.
4. Do not restart IIS, application pools or production services.

## Step 2: Identify IIS Site

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\detect_iis_site.ps1
```

Record:

- IIS site name
- IIS Site ID
- Physical path
- Log file path

## Step 3: Locate W3SVC Logs

Use the IIS Site ID to identify the log folder:

```text
C:\inetpub\logs\LogFiles\W3SVC<site-id>
```

Examples:

```text
Site ID 1 -> C:\inetpub\logs\LogFiles\W3SVC1
Site ID 3 -> C:\inetpub\logs\LogFiles\W3SVC3
```

Confirm:

- Logs exist.
- Logs cover the collection period.
- Logs use W3C format.
- Required W3C fields are present.

## Step 4: Run Diagnostics

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\diagnose_iis_evidence.ps1 `
  -LogRoot "C:\inetpub\logs\LogFiles\W3SVC<site-id>"
```

Check output:

- `available_log_files`
- `detected_w3c_fields`
- `sample_api_requests`
- `api_request_counts.legacy_api`
- `api_request_counts.django_api_v1`

If the result is `IIS_DIAGNOSTIC_NO_API_TRAFFIC`, confirm whether API traffic is
handled by IIS, another reverse proxy, a load balancer, CDN, API gateway or a
different server.

## Step 5: Export Evidence

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\export_iis_api_evidence.ps1 `
  -LogRoot "C:\inetpub\logs\LogFiles\W3SVC<site-id>" `
  -OutputPath "docs\migration\production_evidence\input\iis_api_evidence.csv"
```

Verify:

```text
docs/migration/production_evidence/input/iis_api_evidence.csv
```

The CSV must contain:

```text
timestamp,source,client,endpoint,status_code,user_agent
```

## Step 6: Validate Evidence

Run:

```powershell
python scripts\phase11_1_6_2_1_import_iis_production_data.py
```

Expected with valid evidence:

```text
COMPLETE_EVIDENCE_PACKAGE
```

Then run:

```powershell
python scripts\phase11_1_6_1_final_evidence_validator.py
```

Expected after valid evidence:

```text
READY_FOR_EXECUTION
```

If either command remains blocked, do not execute shutdown.

## Step 7: Upload Evidence Package

Provide these files for architecture review:

```text
docs/migration/production_evidence/input/iis_api_evidence.csv
docs/migration/production_evidence/reports/REAL_PRODUCTION_EVIDENCE_REPORT.json
docs/migration/production_evidence/IIS_COLLECTION_RESULT_TEMPLATE.md
```

If raw IIS logs are allowed to be shared, place reviewed copies in:

```text
docs/migration/production_evidence/input/iis_logs/
```

If raw logs contain sensitive data, store them outside Git and provide only the
approved sanitized CSV/report package.

## Evidence Package Structure

Expected structure:

```text
production_evidence/
├── input/
│   ├── iis_logs/
│   └── iis_api_evidence.csv
├── reports/
│   ├── REAL_IIS_PRODUCTION_TRAFFIC_REPORT.json
│   └── REAL_PRODUCTION_EVIDENCE_REPORT.json
└── approvals/
```

## Stop Conditions

Stop evidence collection and ask for review if:

- Logs are missing.
- Required W3C fields are missing.
- API traffic appears outside IIS.
- Unknown clients are detected.
- Legacy `/api/*` traffic is still present.
- Evidence contains sensitive data that has not been approved for sharing.

## Final Safety Reminder

This runbook does not authorize shutdown. It only prepares production evidence
for review.
