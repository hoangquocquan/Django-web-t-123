# Phase 11.1.1 - Django API Replacement Completion

## Objective

Complete Django API replacements for remaining legacy API routes before legacy
API decommission.

## Scope

- Implement missing Django `/api/v1/...` endpoints.
- Validate compatibility with legacy API route groups.
- Keep legacy routes active.
- Document replacement coverage and remaining operational risks.

## DO NOT

- Do not disable legacy API routes yet.
- Do not remove legacy API code.
- Do not change production routing.
- Do not delete compatibility layer.

## Implementation Tasks

- Audit remaining legacy API routes.
- Implement replacement endpoints for contact, quote, product writes, AI, demo,
  OpenAPI, version, home, news and capabilities.
- Add compatibility tests.
- Add replacement validation script.
- Update compatibility matrix and review package.

## Testing Requirements

- `python scripts\phase11_1_1_api_replacement_validation.py`
- `python manage.py check`
- `pytest django_backend\tests\test_api_compatibility_phase11_1_1.py`
- `pytest`
- `powershell -ExecutionPolicy Bypass -File scripts\run_migration_test.ps1`

## Git Requirements

- Branch: `migration/phase-11.1.1-api-replacement-completion`
- Commit: `feat: complete django api replacements`
- Tag: `phase-11.1.1-api-replacement-complete`

## Review Package Requirements

- `docs/reviews/PHASE_11.1.1_CHANGESET.patch`
- `docs/reviews/PHASE_11.1.1_REVIEW_SUMMARY.md`

## Expected Output

Final status: `WAITING FOR ARCHITECT REVIEW`.
