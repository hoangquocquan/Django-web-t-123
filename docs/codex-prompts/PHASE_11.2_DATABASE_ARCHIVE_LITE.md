# TASK: Phase 11.2 - Legacy Database Archive Lite

Project:

mecprecision-vietnam

## Objective

Create a lightweight archive workflow for the legacy database.

The purpose is to learn the enterprise database retirement process:

Backup -> Verification -> Archive -> Retention -> Rollback planning

## Current Status

Legacy API training shutdown:

`TRAINING_SHUTDOWN_COMPLETE`

## Important Rules

Do not:

- delete database
- destroy data
- modify production database
- execute irreversible migration

Only:

- create archive workflow
- create backup checkpoint
- verify archive integrity
- document process

## Required Documents To Read

- docs/reviews/PHASE_11_FINAL_REVIEW_REPORT.md
- docs/reviews/PHASE_11.1.6.8_TRAINING_SHUTDOWN_REPORT.md
- docs/migration/LEGACY_API_DECOMMISSION_ROLLBACK.md

## Implementation Tasks

1. Create database archive plan.
2. Create archive metadata.
3. Create backup simulation tool.
4. Create verification tool.
5. Create archive report.
6. Create database rollback plan.
7. Create automated tests.
8. Run required validation commands.

## Required Outputs

- docs/reviews/PHASE_11.2_DATABASE_ARCHIVE_PLAN.md
- docs/migration/database_archive/archive_metadata.json
- scripts/phase11_2_database_archive_backup.py
- scripts/phase11_2_database_archive_verify.py
- docs/reviews/PHASE_11.2_DATABASE_ARCHIVE_REPORT.md
- docs/reviews/PHASE_11.2_DATABASE_ROLLBACK_PLAN.md
- tests/test_phase11_2_database_archive_lite.py

## Expected Result

`DATABASE_ARCHIVE_COMPLETE`

## Final Status

PHASE_11_COMPLETE

READY_FOR_PHASE_12
