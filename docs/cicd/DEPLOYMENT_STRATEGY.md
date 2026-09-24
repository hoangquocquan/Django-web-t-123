# Deployment Strategy

## Deployment Options

## Blue/Green Deployment

Blue/Green keeps two environments:

- Blue: current live version.
- Green: new version.

Flow:

1. Deploy new version to green.
2. Run health checks.
3. Switch traffic if green is healthy.
4. Keep blue available for rollback.

Best for:

- Production releases.
- API cutovers.
- Low downtime.

## Rolling Deployment

Rolling deployment updates instances gradually.

Flow:

1. Take one instance out of rotation.
2. Deploy new version.
3. Run health check.
4. Return it to service.
5. Repeat.

Best for:

- Multi-instance environments.
- Lower infrastructure cost than blue/green.

## Manual Deployment

Manual deployment remains acceptable for early staging until automation is
trusted.

Required:

- Checklist.
- Backup.
- Rollback plan.
- Post-deployment validation.

## Rollback

Rollback must be prepared before deployment starts.

Rollback options:

- Repoint traffic to previous blue environment.
- Redeploy previous artifact.
- Restore previous configuration.
- Restore database only when a documented database rollback plan exists.

## Health Validation

Required health checks:

- Application responds.
- `/api/health/` responds.
- `/api/v1/health/` responds.
- Database connectivity passes.
- Error rate stays within threshold.
- Monitoring receives data.

## Production Boundary

Phase 13.0 does not deploy anything. It defines strategy only.

