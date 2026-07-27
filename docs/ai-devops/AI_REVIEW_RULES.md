# AI Review Rules

## Purpose

These rules tell the AI reviewer what to check and what it must never decide on
its own.

## Required Checks

### Documentation Completeness

- Phase prompt exists.
- Architecture or implementation document exists.
- Review summary exists.
- Generated reports are present and readable.

### Test Coverage

- Phase-specific tests exist.
- Regression test command is recorded.
- Test result is included in the review input.

### Security Risks

- No secrets are committed.
- No `.env` files are included.
- No production credentials are included in reports.
- AI prompt input excludes private customer data.

### Production Safety

- No production deployment was executed.
- No production approval is generated automatically.
- No route, proxy, IIS, Nginx, or database production change is performed.

### Rollback Availability

- Rollback strategy or safety boundary is documented.
- Git commit and tag are traceable.
- Blocking conditions are clearly reported.

## Decision Rules

| Decision | Meaning |
| --- | --- |
| PASS | Required validation passed and no blocking risk found. |
| PASS_WITH_WARNING | Validation passed but one or more non-blocking warnings exist. |
| BLOCKED | Required artifact, test, or safety control is missing. |

## Hard Prohibitions

The AI reviewer must not:

- approve production deployment
- disable legacy services
- modify production systems
- bypass human review
- expose secrets in generated reports
- claim real monitoring is deployed when only documentation exists

