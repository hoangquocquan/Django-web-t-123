# Phase 13.1 Docker Build Report

## Build Result

`python scripts/phase13_1_docker_build.py` was run after Docker environment recovery.

Result:

```text
DOCKER_BUILD_COMPLETE
```

Image:

```text
mecprecision-vietnam:phase-13.1
```

Image ID:

```text
sha256:7d491f07e384bdb1dc76d3363bb8e18b408cbcb5bde6e57dbf78b7c0f275c501
```

Image size:

```text
73365727 bytes
```

Docker engine:

```text
Docker Desktop 4.74.0 / Docker Engine 29.4.3
```

Build evidence:

```text
docs/docker/docker_build_report.json
```

## Environment Recovery

Initial issue:

- Docker CLI was installed.
- Docker daemon was initially unavailable.
- Docker config access was denied for the sandbox user:

```text
C:\Users\hoang\.docker\config.json
```

Additional permission detail:

- Current command user could not read `C:\Users\hoang\.docker`.
- Current command user could not access the Docker named pipe without elevated execution.
- `docker-users` contained the Windows user `QUANPC\hoang`, while the command sandbox user was separate.

Recovery action:

- Docker Desktop was started locally.
- Docker commands were run with a temporary `DOCKER_CONFIG` path to avoid modifying or deleting the existing user Docker configuration.
- No Docker configuration was deleted.
- No production configuration was changed.

Temporary Docker config used during validation:

```text
%TEMP%\codex-docker-config
```

## Image Information

- Non-root runtime user: `appuser`
- Exposed port: `8000/tcp`
- Healthcheck: present
- Registry push: not executed
- Production deploy: not executed

## Build Context Fix

The first recovered build attempt failed because Docker could not read a nested `.pytest_cache` directory while preparing the build context.

Fix:

- Added nested cache/log exclusions to `.dockerignore`.
- Removed the Dockerfile `SECRET_KEY` environment default so secrets are not baked into the image layer.
- These changes are Docker/build configuration only and do not modify business logic.

## Validation Result

`python scripts/phase13_1_docker_validate.py` was run after validation hardening.

Result:

```text
DOCKER_VALIDATION_COMPLETE
```

Validation evidence:

```text
docs/docker/docker_validation_report.json
```

Container validation:

- Container started successfully.
- Django health endpoint returned success.
- Health check passed on attempt 2 of 15.
- Validation container was removed after test completion.

Endpoint checked inside the container:

```text
http://127.0.0.1:8000/api/v1/health/
```

## Security Assessment

- Dockerfile uses a non-root user.
- Dockerfile defines a health check.
- Docker Compose separates web, database, and Redis services.
- Compose uses named volumes and a dedicated bridge network.
- No registry credentials are defined.
- No production deployment is executed.

## Testing

Commands run:

```text
pytest tests\test_phase13_1_docker_build.py
pytest
powershell -ExecutionPolicy Bypass -File scripts\run_migration_test.ps1
```

Results:

- Phase 13.1 Docker tests: 5 passed.
- Project regression tests: 139 passed.
- Migration test standard: `MIGRATION TEST PASSED`.
- Django migrated module regression inside migration script: 238 passed.

## Known Issues

- Docker availability still depends on the local machine.
- Normal sandbox access to `C:\Users\hoang\.docker` remains restricted.
- Normal sandbox access to the Docker named pipe remains restricted.
- Elevated local execution plus temporary `DOCKER_CONFIG` was required for Docker validation in this environment.
- If Docker daemon is unavailable later, scripts still produce a blocked-safe report.
- PostgreSQL service is prepared for future CI/staging use but not required by
  the current local SQLite migration backend.
- Docker Desktop or Docker Engine must be started before image build/validation.

## Final Status

DOCKER_BUILD_COMPLETE
