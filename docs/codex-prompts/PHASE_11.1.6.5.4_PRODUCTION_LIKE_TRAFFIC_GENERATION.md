# Phase 11.1.6.5.4 - Production Like Traffic Evidence Generation

## Objective

Create production-like traffic evidence environment for migration validation.

## Purpose

Simulate the enterprise migration evidence flow:

Traffic Generation -> IIS W3C Compatible Logs -> Evidence Collector -> Traffic
Analysis -> Readiness Validation

## Important Rules

Do not:

- execute Legacy API shutdown
- disable `/api` routes
- modify production IIS
- modify proxy
- modify database
- bypass validators

Only:

- generate training traffic
- generate training evidence
- validate migration workflow

## Scripts

Create:

- `scripts/phase11_1_6_5_4_generate_production_like_traffic.py`
- `scripts/phase11_1_6_5_4_generate_iis_logs.py`

Traffic generator requirements:

- generate `1000-5000` replacement `/api/v1/*` requests
- keep legacy `/api/*` requests at `0`
- support `--requests`
- support `--clients`
- support `--days`
- write `docs/migration/production_evidence/handover/traffic_generation_summary.json`

IIS log generator requirements:

- write `docs/migration/production_evidence/input/iis_logs/u_ex_training.log`
- use IIS W3C compatible format
- include `date`, `time`, `c-ip`, `cs-uri-stem`, `sc-status`, `cs(User-Agent)`

## Metadata

Generate:

`docs/migration/production_evidence/handover/collection_metadata.json`

Required values:

- server: `TRAINING-IIS-SERVER`
- environment: `STAGING_SIMULATION`
- iis_site: `MECPrecision-Web`
- site_id: `1`
- operator: `training-user`
- reviewer: `architect-review`

## Testing

Run:

- `python scripts/phase11_1_6_5_4_generate_production_like_traffic.py`
- `python scripts/phase11_1_6_5_4_generate_iis_logs.py`
- `python scripts/phase11_1_6_5_production_evidence_validator.py`
- `pytest tests/test_phase11_1_6_5_4_traffic_generation.py`
- `pytest`
- `powershell -ExecutionPolicy Bypass -File scripts/run_migration_test.ps1`

Expected:

`COMPLETE_EVIDENCE_PACKAGE`

## Git

Branch:

`migration/phase-11.1.6.5.4-production-like-traffic`

Commit:

`feat: add production like traffic evidence generation`

Tag:

`phase-11.1.6.5.4-production-evidence-ready`

## Final Status

`READY_FOR_FINAL_READINESS_VALIDATION`

Stop. Do not execute shutdown. Do not start Phase 11.2.
