# Phase 11.1.6.2 - Real Production Evidence Validation

## Project

mecprecision-vietnam

## Objective

Collect and validate real production traffic evidence to unlock Legacy API
shutdown.

Target transition:

```text
INCOMPLETE_EVIDENCE_PACKAGE -> COMPLETE_EVIDENCE_PACKAGE
```

## Important Rules

Do not:

- Disable Legacy API.
- Modify IIS.
- Modify proxy.
- Change routes.
- Execute shutdown.

Only:

- Collect evidence.
- Analyze logs.
- Validate migration status.

## Input

Evidence files are read from:

```text
docs/migration/production_evidence/input/
```

Supported formats:

- IIS W3C logs
- CSV exports
- JSON logs
- JSONL logs
- API gateway text logs

## Output

The workflow writes:

```text
docs/migration/production_evidence/reports/REAL_PRODUCTION_EVIDENCE_REPORT.json
```

## Validation Rules

- Legacy `/api/*` request count must be `0`.
- Replacement `/api/v1/*` request count must be greater than `0`.
- Unknown clients must be `0`.

## Testing Requirements

Run:

```powershell
python scripts\phase11_1_6_1_final_evidence_validator.py
pytest
powershell -ExecutionPolicy Bypass -File scripts\run_migration_test.ps1
```

Expected without production data:

```text
BLOCKED_SAFELY
```

Expected with valid evidence:

```text
COMPLETE_EVIDENCE_PACKAGE
```

## Git Requirements

Branch:

```text
migration/phase-11.1.6.2-real-production-evidence
```

Commit:

```text
feat: validate real production api migration evidence
```

Tag:

```text
phase-11.1.6.2-evidence-complete
```

## Final Status

`WAITING_FOR_ARCHITECT REVIEW`

Do not start shutdown and do not start Phase 11.2.
