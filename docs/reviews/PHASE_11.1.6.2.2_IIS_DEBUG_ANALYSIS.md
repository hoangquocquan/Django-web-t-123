# Phase 11.1.6.2.2 IIS Debug Analysis

## Phase

Phase 11.1.6.2.2 - IIS Evidence Collector Debug

## Current Issue

The current evidence file contains zero records:

```text
docs/migration/production_evidence/input/iis_api_evidence.csv
```

Because the CSV has no records, production migration evidence cannot prove that
legacy `/api/*` traffic is zero and replacement `/api/v1/*` traffic is active.

## Current Collector Reviewed

```text
scripts/windows/export_iis_api_evidence.ps1
scripts/phase11_1_6_2_real_production_evidence.py
```

The prompt also references:

```text
scripts/phase11_1_6_2_1_import_iis_production_data.py
```

That entrypoint was missing, so this phase adds a compatibility wrapper that
runs the existing Phase 11.1.6.2 evidence workflow.

## Possible Root Causes

| Issue | Status | Detail |
|---|---|---|
| Wrong IIS log directory | Possible | If `-LogRoot` points at the wrong `W3SVC*` folder, no API rows are exported |
| Missing W3C `#Fields:` header | Possible | Rows cannot be mapped without field names |
| Missing `cs-uri-stem` | Possible | API endpoint cannot be detected |
| Wrong column index | Improved | Parser now uses field names and whitespace-safe splitting |
| URI parsing issue | Improved | Parser now detects `^/api(/|$)` instead of only wildcard matching |
| Encoding issue | Reduced | Collector no longer forces UTF-8 for reading IIS logs |
| Empty input handling | Improved | Collector reports W3C field count, missing URI fields and invalid rows |

## Parser Improvements

The PowerShell collector now:

- Trims lines before parsing.
- Handles extra spaces between W3C columns.
- Reports files with `#Fields:` headers.
- Reports missing `cs-uri-stem`.
- Counts invalid rows.
- Detects both `/api/*` and `/api/v1/*` using regex.
- Keeps output CSV creation even when no records are found.

## Diagnostic Tool

Added:

```text
scripts/windows/diagnose_iis_evidence.ps1
```

It reports:

- IIS log path.
- Available log files.
- Detected W3C fields.
- Sample API requests.
- Legacy and Django API request counts.

## Current Evidence Status

```text
INCOMPLETE_EVIDENCE_PACKAGE
```

No real IIS log records are available in the repository, so shutdown remains
blocked safely.
