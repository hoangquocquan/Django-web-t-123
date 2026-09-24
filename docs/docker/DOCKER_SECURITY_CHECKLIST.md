# Docker Security Checklist

## Non-Root User

- The Dockerfile creates and uses `appuser`.
- The application process does not run as root.

## Minimal Image

- Base image: `python:3.12-slim`.
- System packages are kept minimal.
- Apt cache is removed after installation.

## Secret Handling

- No real registry credentials are stored in the repository.
- No production `.env` file is copied into the image.
- Default secrets in Dockerfile and Compose are local placeholders only.
- CI must inject secrets at runtime from a secret manager in future phases.

## Image Scanning

Future CI stages should add:

- Docker image vulnerability scan.
- Dependency scan.
- Secret scan.
- Base image freshness check.

## Network Security

- Compose services communicate on `mecprecision-local`.
- Only the web service exposes a host port.
- Database and Redis are internal to the Compose network by default.

## Build Safety

- Phase 13.1 builds locally only.
- No image is pushed externally.
- No production deployment is executed.
- Build artifacts must include image tag, commit hash, and validation result.

