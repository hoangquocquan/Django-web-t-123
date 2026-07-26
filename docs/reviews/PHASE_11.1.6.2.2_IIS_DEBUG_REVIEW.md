# Phase 11.1.6.2.2 IIS Debug Review

## Phase

Phase 11.1.6.2.2 - IIS Evidence Collector Debug

## Root Cause

Current local root cause:

```text
No IIS production log files are available at C:\inetpub\logs\LogFiles.
```

Diagnostic result:

```text
IIS_DIAGNOSTIC_NO_API_TRAFFIC
```

The existing evidence CSV has zero rows because no readable IIS API traffic
records are present in the repository/local machine.

Additional collector weaknesses found and addressed:

- The collector did not report enough detail when `#Fields:` was missing.
- Missing `cs-uri-stem` was not surfaced clearly.
- W3C rows with extra spaces could shift column mapping.
- API detection used wildcard matching instead of an explicit `/api` regex.
- The expected Python import entrypoint was missing.

## Files Changed

Added:

- `docs/codex-prompts/PHASE_11.1.6.2.2_IIS_EVIDENCE_COLLECTOR_DEBUG.md`
- `docs/reviews/PHASE_11.1.6.2.2_IIS_DEBUG_ANALYSIS.md`
- `docs/reviews/PHASE_11.1.6.2.2_IIS_DEBUG_REVIEW.md`
- `scripts/phase11_1_6_2_1_import_iis_production_data.py`
- `scripts/windows/diagnose_iis_evidence.ps1`
- `tests/test_phase11_1_6_2_2_iis_debug.py`

Modified:

- `scripts/windows/export_iis_api_evidence.ps1`
- `docs/migration/production_evidence/reports/REAL_PRODUCTION_EVIDENCE_REPORT.json`

## Parser Status

```text
IIS_PARSER_HARDENED
```

The IIS collector now supports:

- IIS W3C `#Fields:` headers.
- `date`, `time`, `c-ip`, `cs-uri-stem`, `sc-status`, `cs(User-Agent)`.
- Missing fields without crashing.
- Extra spaces in W3C rows.
- Empty logs.
- Invalid rows.
- Detection of both `/api/*` and `/api/v1/*`.

## Evidence Status

```text
INCOMPLETE_EVIDENCE_PACKAGE
```

Current counts:

| Metric | Count |
|---|---:|
| Legacy `/api/*` rows | 0 |
| Django `/api/v1/*` rows | 0 |
| Unknown clients | 0 |

Reason:

- No evidence records were found.
- Django `/api/v1/*` traffic was not confirmed.

## Test Result

Commands run:

```powershell
python scripts\phase11_1_6_2_1_import_iis_production_data.py
python scripts\phase11_1_6_1_final_evidence_validator.py
powershell -ExecutionPolicy Bypass -File scripts\windows\diagnose_iis_evidence.ps1
pytest tests\test_phase11_1_6_2_2_iis_debug.py
pytest
powershell -ExecutionPolicy Bypass -File scripts\run_migration_test.ps1
```

Results:

- IIS import wrapper: `INCOMPLETE_EVIDENCE_PACKAGE`
- Final evidence validator: `BLOCKED_SAFELY`
- IIS diagnostic: `IIS_DIAGNOSTIC_NO_API_TRAFFIC`
- Phase 11.1.6.2.2 tests: 5 passed
- Root pytest: 22 passed
- Migration test: `MIGRATION TEST PASSED`
- Django full regression inside migration script: 238 passed

## Next Action

Run the diagnostic tool on the actual IIS production server:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\diagnose_iis_evidence.ps1 `
  -LogRoot "C:\inetpub\logs\LogFiles\W3SVC<site-id>"
```

Then export evidence:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\export_iis_api_evidence.ps1 `
  -LogRoot "C:\inetpub\logs\LogFiles\W3SVC<site-id>" `
  -OutputPath "docs\migration\production_evidence\input\iis_api_evidence.csv"
```

Finally import and validate:

```powershell
python scripts\phase11_1_6_2_1_import_iis_production_data.py
python scripts\phase11_1_6_1_final_evidence_validator.py
```

## Safety

No IIS configuration, proxy, API route, database or shutdown execution was
performed.

## Status

```text
WAITING_FOR_ARCHITECT REVIEW
```

Do not execute shutdown and do not start Phase 11.2.
