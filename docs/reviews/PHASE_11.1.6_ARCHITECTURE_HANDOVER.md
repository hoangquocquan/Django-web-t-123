# Phase 11.1.6 Architecture Handover

## Before Migration Architecture

Before decommission readiness, clients may still call legacy `/api/*` routes
served by the legacy Python system. Django `/api/v1/*` exists as the replacement
API surface, but production traffic evidence must prove clients no longer need
legacy `/api/*`.

```mermaid
flowchart LR
  Client["Client / Integration"] --> Legacy["Legacy Python API /api/*"]
  Client --> Django["Django API /api/v1/*"]
  Legacy --> LegacyDb["Legacy data / compatibility layer"]
  Django --> DjangoServices["Django services"]
```

## After Migration Architecture

After a future approved shutdown, clients should use Django `/api/v1/*`.
Legacy `/api/*` is disabled at routing/proxy level only after real evidence and
real approvals pass.

```mermaid
flowchart LR
  Client["Client / Integration"] --> Django["Django API /api/v1/*"]
  Django --> Services["Django service layer"]
  Legacy["Legacy /api/*"] -. "disabled only after approval" .-> Stop["Not served"]
```

## Legacy API Role

Legacy `/api/*` remains available until production evidence proves it has zero
traffic and all approval gates are complete. Legacy code is not deleted during
the rollback window.

## Django API Role

Django `/api/v1/*` is the replacement API. It must show real production traffic
before shutdown can be considered. The expected production success decision is
`READY_TO_EXECUTE_PRODUCTION`.

## Traffic Flow

| Flow | Current Status |
| --- | --- |
| Training simulation traffic | Accepted only for `READY_TO_EXECUTE_TRAINING` |
| Real production traffic | Required for `READY_TO_EXECUTE_PRODUCTION` |
| Simulation in production gate | `BLOCKED_SAFELY` |
| Unknown clients | Must be `0` |
| Legacy `/api/*` traffic | Must be `0` |

## Rollback Architecture

Rollback restores previous router/proxy behavior for `/api/*` while keeping
`/api/v1/*` online. Rollback does not require database schema changes.

```mermaid
flowchart TD
  Failure["Post-shutdown failure detected"] --> Decision["Rollback owner decides"]
  Decision --> Restore["Restore previous /api/* route"]
  Restore --> Smoke["Run health and contract smoke tests"]
  Smoke --> Monitor["Monitor traffic, errors and latency"]
  Monitor --> Record["Record rollback report"]
```

## Architecture Boundary

Phase 11.1.6 provides readiness framework and documentation only. It does not
perform production route changes, IIS changes, proxy changes or database changes.
