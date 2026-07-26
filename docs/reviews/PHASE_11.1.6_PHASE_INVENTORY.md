# Phase 11.1.6 Phase Inventory

## Scope

This inventory classifies Phase 11.1.6 artifacts for Legacy API shutdown
readiness. The current repository state supports training validation only.
Production shutdown remains blocked.

## Inventory

| Phase | Purpose | Status | Evidence Type | Approval Type | Risk Level |
| --- | --- | --- | --- | --- | --- |
| 11.1.6 | Legacy API decommission execution framework | Framework complete, execution blocked | REAL_PRODUCTION required | REAL_APPROVAL required | High |
| 11.1.6.1 | Evidence and approval unlock framework | Framework complete, approvals pending | REAL_PRODUCTION required | REAL_APPROVAL required | High |
| 11.1.6.2 | Real production evidence validation framework | Framework complete, evidence originally incomplete | REAL_PRODUCTION required | REAL_APPROVAL required later | High |
| 11.1.6.2.2 | IIS evidence collector debug | Parser/debug support complete | REAL_PRODUCTION supported | Not applicable | Medium |
| 11.1.6.2.3 | IIS production collection checklist | Documentation complete | REAL_PRODUCTION required | REAL_APPROVAL required later | Medium |
| 11.1.6.3 | Approval package framework | Templates exist, unsigned | REAL_PRODUCTION required | REAL_APPROVAL pending | High |
| 11.1.6.4 | Final readiness gate | Production decision remains `BLOCKED_SAFELY` | REAL_PRODUCTION required | REAL_APPROVAL required | High |
| 11.1.6.4.1 | Final readiness simulation validation | `READY_TO_EXECUTE_TRAINING` only | TRAINING_SIMULATION | SIMULATION_APPROVAL | Medium |
| 11.1.6.5 | Production evidence acquisition framework | Framework complete | REAL_PRODUCTION required | REAL_APPROVAL required later | High |
| 11.1.6.5.1 | Production IIS log collection execution | Checklist/runbook path exists | REAL_PRODUCTION required | Not applicable | Medium |
| 11.1.6.5.2 | Evidence handover package | Handover framework complete | REAL_PRODUCTION required | REAL_APPROVAL required later | Medium |
| 11.1.6.5.3 | Automated IIS evidence collection tool | Tooling complete | REAL_PRODUCTION supported | Not applicable | Medium |
| 11.1.6.5.4 | Production-like traffic simulation | Simulation evidence complete | TRAINING_SIMULATION | SIMULATION_APPROVAL | Medium |
| 11.1.6.6 | Full migration readiness audit | Current audit phase | Mixed audit only | Mixed audit only | High |

## Current Status Files

| File | Purpose | Decision | Classification |
| --- | --- | --- | --- |
| `docs/migration/phase11_1_6_execution/FINAL_READINESS_STATUS.json` | Final readiness gate status | `BLOCKED_SAFELY` | Production readiness status |
| `docs/migration/phase11_1_6_execution/FINAL_READINESS_SIMULATION_STATUS.json` | Training readiness status | `READY_TO_EXECUTE_TRAINING` | Simulation readiness status |
| `docs/migration/production_evidence/reports/REAL_PRODUCTION_TRAFFIC_REPORT.json` | Production pre-shutdown default evidence | `INCOMPLETE_EVIDENCE_PACKAGE` | Real production blocker |
| `docs/migration/production_evidence/reports/REAL_PRODUCTION_EVIDENCE_REPORT.json` | Evidence acquisition output currently produced from simulation data | `COMPLETE_EVIDENCE_PACKAGE` | Training simulation despite filename |

## Key Finding

Simulation readiness and production readiness are separated at the status-file
level. However, the simulation evidence currently lives under
`docs/migration/production_evidence/` and one generated file is named
`REAL_PRODUCTION_EVIDENCE_REPORT.json` while its content says
`environment = STAGING_SIMULATION`. This is a governance risk because operators
could confuse simulation evidence with production evidence.
