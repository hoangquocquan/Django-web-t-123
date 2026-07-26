# Phase 11.1.6.5 Production Evidence Review

## Phase

Phase 11.1.6.5 - Real Production Evidence Acquisition

## Scope

Evidence-only validation. No shutdown, IIS modification, proxy change, route
change, production code change or database change was executed.

## Environment

- Environment: `STAGING_SIMULATION`
- Server: `TRAINING-IIS-SERVER`
- Collection period: `2026-07-19T13:03:28Z - 2026-07-26T12:55:04Z`

## Data Sources

- `C:\Users\hoang\Documents\Codex\mecprecision-vietnam\docs\migration\production_evidence\input\iis_api_evidence.csv`: 1200 records (csv)
- `C:\Users\hoang\Documents\Codex\mecprecision-vietnam\docs\migration\production_evidence\input\iis_logs\u_ex_training.log`: 1200 records (log)

## Traffic Counts

| Metric | Value |
| --- | --- |
| Total API requests | `2400` |
| Legacy `/api/*` requests | `0` |
| Django `/api/v1/*` requests | `2400` |
| Unknown clients | `0` |
| Error requests | `116` |
| Error rate | `0.048333` |

## Required File Check

- IIS logs found: `1`
- CSV export path: `C:\Users\hoang\Documents\Codex\mecprecision-vietnam\docs\migration\production_evidence\input\iis_api_evidence.csv`
- CSV rows: `1200`

## Errors

- None

## Safety Confirmation

- Legacy routes disabled: `False`
- Routes changed: `False`
- Proxy modified: `False`
- IIS modified: `False`
- Database modified: `False`
- Shutdown executed: `False`

## Decision

`COMPLETE_EVIDENCE_PACKAGE`

## Next Action

Provide real IIS production logs and a non-empty CSV export covering at least 7
days before rerunning the final readiness gate.
