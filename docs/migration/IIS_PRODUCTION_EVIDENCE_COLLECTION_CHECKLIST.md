# IIS Production Evidence Collection Checklist

## Purpose

Use this checklist on the production Windows Server before Legacy API shutdown.
The checklist is evidence-only. It must not modify IIS, restart services,
change routing, disable Legacy API or execute shutdown.

## Server Information

- [ ] Server name:
- [ ] Environment:
- [ ] IIS site name:
- [ ] IIS Site ID:
- [ ] Collection date:
- [ ] Operator:
- [ ] Evidence reviewer:

## IIS Log Verification

- [ ] IIS Logging enabled
- [ ] Format W3C
- [ ] Log directory confirmed
- [ ] W3SVC folder confirmed
- [ ] Read permission confirmed
- [ ] Logs cover the approved observation period

Required W3C fields:

- [ ] `date`
- [ ] `time`
- [ ] `c-ip`
- [ ] `cs-uri-stem`
- [ ] `sc-status`
- [ ] `cs(User-Agent)`

Recommended W3C fields:

- [ ] `cs-method`
- [ ] `cs-uri-query`
- [ ] `s-ip`
- [ ] `s-port`

## Log Collection

- [ ] Copy IIS logs into `docs/migration/production_evidence/input/iis_logs/`
- [ ] Verify date range
- [ ] Verify file size
- [ ] Verify no corruption
- [ ] Verify files are readable
- [ ] Verify raw logs are stored securely outside Git when required

## API Analysis

Check Legacy API:

```text
/api/*
```

Check replacement Django API:

```text
/api/v1/*
```

Record:

- [ ] Legacy request count:
- [ ] Django request count:
- [ ] Unknown clients:
- [ ] Error request count:
- [ ] Collection period:

## Evidence Export

Run diagnostics:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\diagnose_iis_evidence.ps1 `
  -LogRoot "C:\inetpub\logs\LogFiles\W3SVC<site-id>"
```

Run export:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\export_iis_api_evidence.ps1 `
  -LogRoot "C:\inetpub\logs\LogFiles\W3SVC<site-id>" `
  -OutputPath "docs\migration\production_evidence\input\iis_api_evidence.csv"
```

Verify:

- [ ] `docs/migration/production_evidence/input/iis_api_evidence.csv` exists
- [ ] CSV has header `timestamp,source,client,endpoint,status_code,user_agent`
- [ ] CSV contains expected API rows
- [ ] `/api/v1/*` rows are present
- [ ] `/api/*` legacy rows are counted

## Evidence Validation

Import evidence:

```powershell
python scripts\phase11_1_6_2_1_import_iis_production_data.py
```

Validate final evidence gate:

```powershell
python scripts\phase11_1_6_1_final_evidence_validator.py
```

Required before shutdown can be considered:

```text
COMPLETE_EVIDENCE_PACKAGE
READY_FOR_EXECUTION
```

## Decision

- [ ] `COMPLETE_EVIDENCE_PACKAGE`
- [ ] `INCOMPLETE_EVIDENCE_PACKAGE`

Decision notes:

```text
PENDING
```

## Safety Confirmation

- [ ] Legacy API was not disabled
- [ ] IIS configuration was not modified
- [ ] Routing was not changed
- [ ] Production services were not restarted
- [ ] Shutdown was not executed
