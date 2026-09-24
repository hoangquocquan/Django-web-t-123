# Phase 11.1.6.5.3 - IIS Automated Evidence Collection Tool

## Objective

Create a one-click IIS production evidence collection tool for Windows Server
administrators.

## Important Rules

Do not:

- shutdown Legacy API
- disable routes
- modify IIS configuration
- modify proxy
- modify database

Only:

- collect evidence
- generate reports
- validate data

## Tool

Create:

`scripts/windows/Collect-IIS-Production-Evidence.ps1`

## Required Functions

The script must:

1. Detect IIS installation.
2. Detect IIS websites and output site name/site ID.
3. Locate IIS logs at `C:\inetpub\logs\LogFiles\W3SVC<SITE_ID>`.
4. Validate W3C logging.
5. Collect logs, default last 7 days, optional `-Days 30`.
6. Create evidence package under `docs/migration/production_evidence/`.
7. Generate `collection_metadata.json`.
8. Export `iis_api_evidence.csv`.
9. Run validator automatically.

## Documentation

Create:

`docs/migration/AUTOMATED_IIS_EVIDENCE_COLLECTION_GUIDE.md`

## Testing

Run:

- `pytest tests/test_phase11_1_6_5_3_iis_automation.py`
- `pytest`
- `powershell -ExecutionPolicy Bypass -File scripts/run_migration_test.ps1`

## Git

Branch:

`migration/phase-11.1.6.5.3-iis-automation-tool`

Commit:

`feat: add automated IIS production evidence collector`

Tag:

`phase-11.1.6.5.3-iis-automation-ready`

## Final Status

`WAITING_FOR_REAL_IIS_EVIDENCE`

Stop. Do not execute shutdown. Do not start Phase 11.2.
