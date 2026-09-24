# Deployment Runbook

## Pre-Deployment Checklist

- Confirm tests passed.
- Confirm Docker image exists.
- Confirm rollback artifact reference is known.
- Confirm no production target is configured.
- Confirm secrets are not stored in Git.

## Deployment Steps

Local simulation:

```powershell
python scripts/phase13_4_deploy.py
```

The script starts a local container from the approved Docker image and writes:

```text
docs/deployment/deployment_result.json
```

## Validation Steps

Run:

```powershell
python scripts/phase13_4_health_check.py
```

Checks:

- container status
- application endpoint
- database status from health response
- critical dependency evidence

## Failure Handling

If deployment or health check fails:

1. Do not promote the artifact.
2. Review deployment evidence.
3. Run rollback simulation.
4. Fix the failing stage.
5. Repeat tests before another deployment attempt.

## Rollback Steps

Run:

```powershell
python scripts/phase13_4_rollback.py
```

The rollback script restores the previous artifact reference in evidence and
cleans up the local simulation container when present.

## Production Boundary

This runbook does not deploy production and does not create cloud resources.
