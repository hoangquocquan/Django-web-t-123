# Evidence Classification Standard

## Purpose

This standard prevents training artifacts from being misunderstood as real
production evidence during Legacy API shutdown readiness checks.

## Evidence Types

| Evidence Type | Meaning | Allowed Decision |
| --- | --- | --- |
| `REAL_PRODUCTION_EVIDENCE` | Evidence collected from real production IIS/API traffic. | May unlock `READY_TO_EXECUTE_PRODUCTION` only after all approvals pass. |
| `STAGING_SIMULATION_EVIDENCE` | Production-like training data generated for workflow validation. | May unlock `READY_TO_EXECUTE_TRAINING` only. |
| `DEVELOPMENT_TEST_EVIDENCE` | Local or development data for test coverage. | Never unlock production. |

## Required Metadata

Every evidence report must include:

| Field | Required Value For Production | Example |
| --- | --- | --- |
| `environment` | `production`, `prod` or `real_production` | `production` |
| `simulation` | `false` | `false` |
| `source` | Real source name | `iis_w3c_logs_and_csv` |
| `collection_period` | Real collection window | `2026-07-20 to 2026-07-26` |
| `approved_by` | Real reviewer or approval reference | `ops-owner` |

## Simulation Metadata

Simulation reports must include:

```json
{
  "simulation": true,
  "environment": "STAGING_SIMULATION",
  "source": "iis_w3c_logs_and_csv",
  "collection_period": "training-window",
  "approved_by": "architect-review"
}
```

## Naming Rules

Use production-safe names only for real production evidence:

- `REAL_PRODUCTION_TRAFFIC_REPORT.json`
- `REAL_IIS_PRODUCTION_TRAFFIC_REPORT.json`

Use simulation-safe names for generated or training evidence:

- `SIMULATION_PRODUCTION_EVIDENCE_REPORT.json`
- `FINAL_READINESS_SIMULATION_STATUS.json`

Do not name simulation artifacts with `REAL_PRODUCTION_*`.

## Readiness Decisions

| Input | Production Gate | Training Gate |
| --- | --- | --- |
| Real production evidence and real approvals | `READY_TO_EXECUTE_PRODUCTION` | Not applicable |
| Staging simulation evidence | `BLOCKED_SAFELY` | `READY_TO_EXECUTE_TRAINING` |
| Missing metadata | `BLOCKED_SAFELY` | `BLOCKED_SAFELY` unless explicitly valid simulation |
| Development evidence | `BLOCKED_SAFELY` | `BLOCKED_SAFELY` |

## Safety Rule

No evidence with `simulation = true` may produce a production readiness decision.
