# Phase 6A Accidental Docker Prune Read-Only Assessment Report

Timestamp: 2026-09-15 Asia/Tokyo

## Final verdict

SAFE_TO_PREPARE_RECOVERY

This was a read-only forensic assessment after accidental `wsl --shutdown` and Docker prune commands. No recovery, cleanup, restart, migration, launcher, staging, commit, or source mutation was performed other than creating this report.

The strongest evidence is that Docker Desktop is now responsive, the only running Compose project is `mecprecision-vietnam`, important named volumes for `mecprecision-vietnam` and AI Factory staging still exist, and the Django Phase 6A worktree is intact. Containers and networks removed by prune are considered recreatable only where a source declaration or runtime configuration exists. Persistent data is not declared safe unless the matching named volume or host bind path still exists.

## Commands Executed

All Docker commands were run through a bounded process wrapper with explicit timeouts. Commands are listed in sanitized form; no environment-variable values or secrets are included.

| Command | Timeout | Purpose |
| --- | ---: | --- |
| `docker version` | 10-15s | Client/server responsiveness |
| `docker info` | 10s | Initial daemon probe; sandbox denied |
| `docker info --format ...` | 15s | Retried read-only probe; unsupported argument form in this CLI |
| `docker ps -a --format ...` | 10-15s | Remaining container inventory |
| `docker volume ls --format ...` | 10-15s | Remaining volume inventory |
| `docker network ls --format ...` | 10-15s | Remaining network inventory |
| `docker image ls --format ...` | 10-15s | Remaining image inventory |
| `docker system df` | 10-15s | Disk/build-cache inventory |
| `docker compose ls -a --format json` | 10-15s | Remaining Compose project inventory |
| `rg --files ...` in Django root | bounded by tool timeout | Compose/Dockerfile discovery |
| `rg --files ...` in AI Factory root | bounded by tool timeout | Compose/Dockerfile discovery |
| `git rev-parse --show-toplevel` | bounded by tool timeout | Django/AI Factory source check |
| `git branch --show-current` | bounded by tool timeout | Django/AI Factory branch check |
| `git rev-parse HEAD` | bounded by tool timeout | Django/AI Factory HEAD check |
| `git status --short` | bounded by tool timeout | Django/AI Factory worktree preservation |
| `git diff --check` | bounded by tool timeout | Django whitespace/source sanity |
| `Get-Content` for selected compose/docs/config files | bounded by tool timeout | Safe source/config inspection |
| `Get-NetTCPConnection` for ports 8000, 8443, 5432, 5679 | bounded by tool timeout | Host listener check |

One broad text search over `C:\Users\hoang\Documents\Codex` produced excessive output and was not used as report evidence. No follow-up action relied on it.

## Bounded Probe Results

Initial sandboxed Docker probes could not reach the daemon due to Windows permission denial against the Docker pipe. The read-only probes were rerun with escalation because Docker inventory was required and still read-only.

| Probe | Result |
| --- | --- |
| Docker client/server | Responsive after escalation; Docker Desktop 4.74.0, Engine 29.4.3 |
| Docker context | `desktop-linux` in responsive probe |
| Containers | 5 containers remain, all running |
| Volumes | 10 local volumes remain |
| Networks | 5 networks remain |
| Images | 9 repository/tag rows remain; Docker reports 8 image objects |
| Compose projects | 1 project remains: `mecprecision-vietnam`, running 5 services |
| Docker system df | Images 8 total/5 active; containers 5 total/5 active; local volumes 10 total/5 active; build cache 28 entries |
| Host TCP listener probe | No direct listener reported for 8000, 8443, 5432, 5679 by `Get-NetTCPConnection`; Docker still reports published ports for some running containers |

## Remaining Docker Inventory

### Containers

| Name | Image | Status | Docker-level ports | Classification |
| --- | --- | --- | --- | --- |
| `mecprecision-vietnam-web-1` | `mecprecision-vietnam:prod-local` | Up, healthy | `8000->8000/tcp` | VERIFIED_MECPRECISION |
| `mecprecision-vietnam-n8n-1` | `n8nio/n8n:2.21.7` | Up, healthy | `5679->5678/tcp` | VERIFIED_MECPRECISION |
| `mecprecision-vietnam-database-1` | `postgres:16-alpine` | Up, healthy | internal `5432/tcp` | VERIFIED_MECPRECISION |
| `mecprecision-vietnam-redis-1` | `redis:7-alpine` | Up, healthy | internal `6379/tcp` | VERIFIED_MECPRECISION |
| `mecprecision_phase10_dryrun_postgres` | `postgres:16` | Up, healthy | `5432->5432/tcp` | VERIFIED_MECPRECISION |

No `django-web-t-123-phase6` containers remain. No AI Factory staging containers remain in the Docker container inventory.

### Volumes

| Name | Classification | Persistent-data assessment |
| --- | --- | --- |
| `ai-factory-staging-v1-n8ndata` | VERIFIED_AI_FACTORY | INTACT as a named volume; contents not inspected |
| `ai-factory-staging-v1-pgdata` | VERIFIED_AI_FACTORY | INTACT as a named volume; contents not inspected |
| `ai-factory-staging-v1-redisdata` | VERIFIED_AI_FACTORY | INTACT as a named volume; contents not inspected |
| `mecprecision-vietnam_media-data` | VERIFIED_MECPRECISION | INTACT as a named Compose volume |
| `mecprecision-vietnam_n8n-data` | VERIFIED_MECPRECISION | INTACT as a named Compose volume |
| `mecprecision-vietnam_phase10_postgres_dryrun_data` | VERIFIED_MECPRECISION | INTACT as a named Compose volume |
| `mecprecision-vietnam_postgres-data` | VERIFIED_MECPRECISION | INTACT as a named Compose volume |
| `mecprecision-vietnam_redis-data` | VERIFIED_MECPRECISION | INTACT as a named Compose volume |
| `t-i-ang-l-m-d_n8n_data` | AMBIGUOUS | AMBIGUOUS; named n8n-like volume but not tied to the inspected project roots |
| anonymous local volume ID | AMBIGUOUS | AMBIGUOUS; anonymous volume identity cannot prove business value from safe metadata alone |

No `django-web-t-123-phase6-postgres-data` or `django-web-t-123-phase6-media` volume remains. Because Phase 6A live validation never completed, no irreplaceable Phase 6A data is proven to have existed there.

### Networks

| Name | Classification | Assessment |
| --- | --- | --- |
| `bridge` | UNRELATED | Docker default network |
| `host` | UNRELATED | Docker default network |
| `none` | UNRELATED | Docker default network |
| `mecprecision-vietnam_default` | VERIFIED_MECPRECISION | INTACT |
| `mecprecision-vietnam_mecprecision-local` | VERIFIED_MECPRECISION | INTACT |

No `django-web-t-123-phase6-internal` network remains. No AI Factory staging network remains in the Docker network inventory.

### Images

| Repository:Tag | Classification | Assessment |
| --- | --- | --- |
| `ai-factory:staging-validation-v1` | VERIFIED_AI_FACTORY | INTACT image; containers can potentially be recreated if runtime config is available |
| `n8nio/n8n:2.35.7` | AMBIGUOUS | INTACT image; not conclusively bound to inspected source declarations |
| `mecprecision-vietnam:prod-local` | VERIFIED_MECPRECISION | INTACT image |
| `mecprecision-vietnam:phase-13.1` | VERIFIED_MECPRECISION | INTACT image |
| `redis:7-alpine` | VERIFIED_MECPRECISION | INTACT image used by running mecprecision Redis; also suitable for Phase 6A if needed |
| `postgres:16` | VERIFIED_MECPRECISION | INTACT image used by phase10 dry-run PostgreSQL |
| `postgres:16-alpine` | VERIFIED_MECPRECISION | INTACT image used by running mecprecision database; also suitable for Phase 6A if needed |
| `n8nio/n8n:2.21.7` | VERIFIED_MECPRECISION | INTACT image used by running mecprecision n8n |
| `n8nio/n8n:latest` | VERIFIED_MECPRECISION | Same age/image family as running mecprecision n8n; exact tag use remains low-risk but not relied on |

### Build Cache

Docker reports 28 build-cache entries totaling about 745.3 MB. Because build cache is not persistent application data, its loss would be RECREATABLE. The current remaining cache was not inspected beyond `docker system df`.

## Expected Versus Actual Resources

### Django Phase 6A

Source declaration: `docker-compose.phase6.yml`.

| Service | Expected image/build | Expected container | Expected network | Expected named volume/bind | Published host port | Actual state | Recreate/data risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `postgres` | `postgres:16-alpine` | `django-web-t-123-phase6-postgres` | `django-web-t-123-phase6-internal` | `django-web-t-123-phase6-postgres-data` | none | Not present | RECREATABLE; no irreplaceable Phase 6A data proven |
| `redis` | `redis:7-alpine` | `django-web-t-123-phase6-redis` | `django-web-t-123-phase6-internal` | none | none | Not present | RECREATABLE |
| `django` | build from `Dockerfile`, image `django-web-t-123-phase6-django:local` | `django-web-t-123-phase6-django` | `django-web-t-123-phase6-internal` | `django-web-t-123-phase6-media` | loopback `8000` by default | Not present | RECREATABLE; media volume not proven to contain data |

Phase 6A cannot be treated as live-validated yet. Docker currently reports mecprecision publishing port 8000, so Phase 6A recovery should either coordinate that runtime or use an explicit approved alternate Phase 6 port. This task did not start Phase 6A.

### Django repository broader compose stack

Source declaration: `docker-compose.yml`.

| Service | Expected image/build | Expected volume/bind | Actual state | Classification |
| --- | --- | --- | --- | --- |
| `web` | build local, `mecprecision-vietnam:prod-local` | `media-data` | Running healthy | VERIFIED_MECPRECISION |
| `database` | `postgres:16-alpine` | `postgres-data` | Running healthy | VERIFIED_MECPRECISION |
| `redis` | `redis:7-alpine` | `redis-data` | Running healthy | VERIFIED_MECPRECISION |
| `n8n` | `n8nio/n8n:2.21.7` | `n8n-data`, bind `./n8n/workflows` | Running healthy | VERIFIED_MECPRECISION |
| `phase10-postgres-dryrun` | `postgres:16` | `phase10_postgres_dryrun_data` | Running healthy | VERIFIED_MECPRECISION |

### AI Factory

Inspected root: `C:\Users\hoang\Documents\Codex\AI FACTORY`.

Direct compose/Dockerfile declarations were not found in the specified AI Factory root by bounded file discovery. The canonical N8N module exists at `PROJECT\N8N-AI-FACTORY-WORKFLOW-ORCHESTRATOR`, with `package.json`, `README.md`, `N8N_RUNTIME_BINDING_STATUS.md`, and `config\n8n-config.yaml`.

Safe source evidence says:

- Module: `N8N-AI-FACTORY-WORKFLOW-ORCHESTRATOR`
- Status: `CANONICAL_EXECUTABLE_LOCAL_BINDING`, `NOT_DEPLOYED`
- Local N8N runtime availability was previously `BLOCKED`
- Runtime config uses local N8N plus a narrow localhost bridge, not a Docker Compose declaration
- Docker image `ai-factory:staging-validation-v1` remains
- Named staging volumes `ai-factory-staging-v1-n8ndata`, `ai-factory-staging-v1-pgdata`, and `ai-factory-staging-v1-redisdata` remain

| Expected component | Evidence source | Current Docker state | Recreate/data risk |
| --- | --- | --- | --- |
| `web` | Not found as AI Factory compose declaration in specified root | No AI Factory container present | AMBIGUOUS |
| `signer` | Historical/runtime references exist, no direct compose declaration used | No Docker container present | AMBIGUOUS |
| `boundary` | Historical/runtime references exist, no direct compose declaration used | No Docker container present | AMBIGUOUS |
| `namespace` | No direct Docker declaration found | No Docker container present | AMBIGUOUS |
| `n8n` | Canonical module config and package scripts exist | No AI Factory n8n container present; n8n-related named volume remains | RECREATABLE in principle, but exact Docker recreation path not proven from compose |
| Redis | Named staging volume remains | No AI Factory Redis container present | Data volume INTACT, container RECREATABLE only if launcher/config is supplied |
| PostgreSQL | Named staging volume remains | No AI Factory PostgreSQL container present | Data volume INTACT, container RECREATABLE only if launcher/config is supplied |

## Volume And Persistent-Data Assessment

| Area | Status | Evidence |
| --- | --- | --- |
| Mecprecision PostgreSQL data | INTACT | `mecprecision-vietnam_postgres-data` remains and running database is healthy |
| Mecprecision Redis data | INTACT | `mecprecision-vietnam_redis-data` remains and running Redis is healthy |
| Mecprecision n8n data | INTACT | `mecprecision-vietnam_n8n-data` remains and running n8n is healthy |
| Mecprecision media | INTACT | `mecprecision-vietnam_media-data` remains |
| AI Factory n8n staging data | INTACT as volume | `ai-factory-staging-v1-n8ndata` remains; contents not inspected |
| AI Factory PostgreSQL staging data | INTACT as volume | `ai-factory-staging-v1-pgdata` remains; contents not inspected |
| AI Factory Redis staging data | INTACT as volume | `ai-factory-staging-v1-redisdata` remains; contents not inspected |
| Django Phase 6A PostgreSQL/media | RECREATABLE | Phase 6A named volumes not present; live validation had not completed and no irreplaceable data is proven |
| Anonymous Docker volume | AMBIGUOUS | Metadata alone cannot prove purpose or data value |
| `t-i-ang-l-m-d_n8n_data` | AMBIGUOUS | Existing named n8n-like volume but not tied to inspected roots |
| Bind-mounted host data | INTACT where source paths were visible | Docker prune does not remove host bind directories; no host source deletion observed |

No confirmed irreplaceable data loss was found. The main unknown is whether any pruned anonymous or non-present named volume outside the inspected naming patterns contained important data. There is no evidence of that from the current inventory.

## Django Git/Source Assessment

| Check | Result |
| --- | --- |
| Root | `C:/Users/hoang/Documents/ChatGPT/WEB Ô TÔ DJANGO` |
| Branch | `codex/demo-database-validation` |
| HEAD | `01f15037e64d6c565e8444dc99eee6c9eb7c37f4` |
| Expected checkpoint | Matches Phase 6A baseline |
| Worktree | Phase 6A implementation remains modified/untracked as expected |
| `git diff --check` | Passed with CRLF warnings only |
| Staging | No staging action performed in this assessment |

Docker prune did not change Git files. Phase 6A paths remain present as modified or untracked source/report files.

## AI Factory Source/Configuration Assessment

| Check | Result |
| --- | --- |
| Root | `C:/Users/hoang/Documents/Codex/AI FACTORY` |
| Branch | `main` |
| HEAD | `5d4dfd3d71674ee65cf3ca1e7513670543034144` |
| Worktree | Existing large dirty/untracked state remains; not modified by this assessment |
| Canonical N8N module | Present under `PROJECT/N8N-AI-FACTORY-WORKFLOW-ORCHESTRATOR` |
| AI Factory direct compose file in specified root | Not found by bounded discovery |
| Runtime status docs | Present and indicate N8N local runtime binding, not deployed |

AI Factory source/configuration files appear present from safe metadata and selected non-secret docs. No AI Factory launcher was executed.

## Data-Loss Conclusions

| Category | Status | Conclusion |
| --- | --- | --- |
| Containers | RECREATABLE | Prune removed stopped containers; remaining containers are mecprecision. Containers generally do not hold durable data when named volumes/binds are used. |
| Networks | RECREATABLE | Removed unused networks can be recreated from compose/launchers; no network data is persistent. |
| Images | INTACT | Important visible images remain, including mecprecision, postgres, redis, n8n, and `ai-factory:staging-validation-v1`. Missing images would be pull/build-recreatable. |
| Named volumes | INTACT for identified important volumes | Mecprecision and AI Factory staging named volumes remain. Phase 6A volumes are absent but no irreplaceable data is proven. |
| Bind-mounted host data | INTACT | Docker prune does not delete bind-mounted host directories; source checks show roots remain. |
| Git/source files | INTACT | Django and AI Factory Git/source trees remain present. |
| Build cache | RECREATABLE | Remaining build cache exists; any pruned cache is not persistent app data. |

## Evidence-Backed Impact Summary

The accidental prune likely deleted stopped AI Factory staging containers and unused networks. Current evidence does not show important named persistent volumes were deleted. The AI Factory staging data volumes remain by exact name. Mecprecision is currently running and healthy with its named volumes present.

The main operational impact is that stopped/recreatable runtime objects may need to be rebuilt or relaunched from their owning project procedures. The main forensic unknown is any anonymous or unrecognized volume that may have been pruned before this assessment; current evidence cannot prove its prior contents.

Phase 6A remains unvalidated live. Its source implementation remains intact, but no Phase 6A Docker resources are currently present.

## Safest Ordered Recovery Plan

1. Preserve the current Docker state; do not run further prune commands.
2. Export or back up remaining important named volumes before any destructive operation: mecprecision volumes and `ai-factory-staging-v1-*` volumes.
3. Keep `mecprecision-vietnam` running until Owner confirms whether it must stay live, because it currently owns the visible running Docker stack.
4. For AI Factory, identify the authoritative launcher/config that created `ai-factory-staging-v1-*` before recreating containers. Do not initialize new PostgreSQL/Redis/n8n over those volumes without backup.
5. For Phase 6A, choose a safe validation window or explicit alternate port because Docker reports mecprecision publishing port 8000.
6. Rerun the Phase 6A live validation task only after the Owner approves the runtime/port coordination.
7. If any recovery requires container creation, volume mounting, database start, migrations, or n8n initialization, perform that in a separate recovery task with explicit authorization.

## Actions That Remain Forbidden In This Assessment

- No Docker Desktop restart/reset.
- No `wsl --shutdown`.
- No Docker prune of any kind.
- No `docker compose up/down/start/stop/restart`.
- No container/image/volume/network create, remove, start, stop, or mutation.
- No volume content inspection by mounting into a container.
- No database initialization, migration, or application launch.
- No Django, Vite, n8n, AI Factory, Zalo, 9Router, Codex Bridge, or project launcher execution.
- No Git stage, commit, restore, reset, checkout, merge, rebase, push, deploy, tag, or branch change.
- No secret, `.env`, token, password, or environment-value printing.

## Blockers And Unknowns

- Exact pre-prune inventory is unavailable, so deleted anonymous volumes or previously stopped containers cannot be exhaustively named from current Docker state.
- AI Factory Docker topology was not found as a compose declaration in the specified AI Factory root; recovery path must come from its authoritative launcher/config in a separate task.
- `t-i-ang-l-m-d_n8n_data` and the anonymous local volume remain ambiguous.
- Docker reports published ports for running mecprecision containers, while host TCP listener probing did not show direct listeners for the checked ports. Treat Docker's own inventory as authoritative for Docker-level port ownership.
- No volume contents were inspected, by design.

## Final Git State

No files were staged or committed.

The only file intentionally created by this task is:

- `PHASE_6A_ACCIDENTAL_DOCKER_PRUNE_READ_ONLY_ASSESSMENT_REPORT.md`
