# Deployment Security

## Secrets

- Do not commit real secrets.
- Use environment variables or secret managers for real environments.
- Phase 13.4 uses local simulation only.

## Permissions

Deployment automation should run with least privilege:

- Docker access only for local simulation.
- No cloud credentials.
- No production server credentials.

## Approval

Human approval is mandatory for:

- staging promotion
- production deployment
- real rollback

Automation can report. Humans decide.

## Audit Trail

Required evidence:

- deployment result
- health result
- rollback result
- commit hash
- branch
- artifact image

## Rollback Safety

Rollback reference must be recorded before deployment simulation starts.

Rollback must not be removed or overwritten by deployment automation.

## Production Safety

Phase 13.4 confirms:

- production deployed: false
- cloud infrastructure created: false
- production secrets stored: false
- rollback capability removed: false
