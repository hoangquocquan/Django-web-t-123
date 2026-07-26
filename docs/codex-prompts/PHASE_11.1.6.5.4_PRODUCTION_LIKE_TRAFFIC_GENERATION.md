# Phase 11.1.6.5.4 - Production Like Traffic Evidence Generation

## Objective

Create a production-like traffic environment for migration validation.

## Purpose

Simulate the enterprise migration evidence flow:

Traffic -> IIS W3C style logs -> Evidence Collector -> Traffic Report ->
Readiness Gate

## Important Rules

Do not:

- shutdown Legacy API
- disable routes
- modify production configuration
- bypass validation logic

Only:

- generate test traffic
- generate test evidence
- validate migration workflow

## Scripts

Create:

- `scripts/phase11_1_6_5_4_generate_production_like_traffic.py`
- `scripts/phase11_1_6_5_4_generate_iis_evidence.py`

## Testing

Run:

- `python scripts/phase11_1_6_5_4_generate_production_like_traffic.py`
- `python scripts/phase11_1_6_5_4_generate_iis_evidence.py`
- `python scripts/phase11_1_6_5_production_evidence_validator.py`
- `pytest tests/test_phase11_1_6_5_4_traffic_generation.py`
- `pytest`
- `powershell -ExecutionPolicy Bypass -File scripts/run_migration_test.ps1`

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
