# Phase 4D - Order Progress Audit API and Write Boundary Report

## Final verdict

`READY_FOR_PHASE_5`

SQLite/static validation, PostgreSQL 16 validation, focused concurrency tests,
Docker ownership/cleanup, canonical audit integration, and MVP_V1 write-boundary
closure are complete. No commit, push, merge, rebase, amend, deployment, branch
change, reset, or stash was performed.

## Isolation and baseline

- Working directory: `C:\Users\hoang\Documents\ChatGPT\WEB Ô TÔ DJANGO`
- Git root: `C:/Users/hoang/Documents/ChatGPT/WEB Ô TÔ DJANGO`
- Branch: `codex/demo-database-validation`
- Baseline HEAD: `86e2a0f669acd05764ab05bdf1ec7c64524cab16`
- Baseline subject: `phase4c: add quotation and order conversion command APIs`
- Remote: `https://github.com/hoangquocquan/Django-web-t-123.git`

Current changed paths are all Phase 4D-scoped:

- Existing Phase 4D implementation: `django_backend/apps/api/canonical_permissions.py`
- Existing Phase 4D implementation: `django_backend/apps/api/canonical_urls.py`
- Existing Phase 4D implementation: `django_backend/apps/api/serializers/canonical_commands.py`
- Existing Phase 4D implementation: `django_backend/apps/api/services/canonical_command_service.py`
- Existing Phase 4D implementation: `django_backend/apps/api/views/canonical_commands.py`
- Existing Phase 4D implementation: `django_backend/apps/transaction_domain/order_domain.py`
- Existing Phase 4D implementation: `django_backend/apps/transaction_domain/services.py`
- Phase 4D test: `django_backend/apps/api/tests/test_phase4d_order_progress_commands.py`
- Phase 4D report: `PHASE_4D_ORDER_PROGRESS_AUDIT_API_AND_WRITE_BOUNDARY_REPORT.md`

No unrelated changed path was found. AI FACTORY, n8n, Zalo, 9Router, Codex
Bridge, and their reserved ports were not read, inspected, started, stopped, or
modified.

## Endpoint inventory

All command routes are authenticated `POST` routes under `/api/v1/canonical/`.

| Route | Domain command |
| --- | --- |
| `orders/{order_id}/commands/progress/` | `transition_order(..., target_status="IN_PROGRESS")` |
| `orders/{order_id}/commands/hold/` | `transition_order(..., target_status="ON_HOLD")` |
| `orders/{order_id}/commands/resume/` | `transition_order(..., target_status="IN_PROGRESS")` |
| `orders/{order_id}/commands/complete/` | `transition_order(..., target_status="COMPLETED", progress_percent=100)` |
| `orders/{order_id}/commands/cancel/` | `transition_order(..., target_status="CANCELLED")` |

The previously drafted `orders/{order_id}/commands/start-progress/` alias was
removed. No established client, report, URL contract, or compatibility matrix
required it; the focused test now proves it returns 404.

## Permission matrix

Every command requires an active authenticated user, active role, exact
`order:view`, and the exact command permission. Wildcard-only permission does
not satisfy the exact canonical command check.

| Command | Permission | Admin | Manager | Sales | Other roles |
| --- | --- | --- | --- | --- | --- |
| Progress | `order:progress` | Allowed with exact grant | Allowed with exact grant | Denied | Denied |
| Hold | `order:hold` | Allowed with exact grant | Allowed with exact grant | Denied | Denied |
| Resume | `order:resume` | Allowed with exact grant | Allowed with exact grant | Denied | Denied |
| Complete | `order:complete` | Allowed with exact grant | Allowed with exact grant | Denied | Denied |
| Cancel | `order:cancel` | Allowed with exact grant | Allowed with exact grant | Denied | Denied |
| Global audit read | `audit:view` | Allowed with exact grant | Allowed with exact grant | Denied | Denied |

Focused tests cover unauthenticated, inactive user, inactive role, missing exact
`order:view`, missing exact command permission, wildcard-only, unassigned,
unrelated, Sales denied across all order commands, and Admin/Manager exact-grant
requirements.

## Transition matrix

The canonical state machine now supports all required Phase 4D transitions:

| From | To | Result |
| --- | --- | --- |
| `CONFIRMED` | `IN_PROGRESS` | Allowed |
| `CONFIRMED` | `ON_HOLD` | Allowed with reason |
| `CONFIRMED` | `CANCELLED` | Allowed with reason |
| `IN_PROGRESS` | `IN_PROGRESS` | Allowed as a progress-percent update |
| `IN_PROGRESS` | `ON_HOLD` | Allowed with reason |
| `IN_PROGRESS` | `COMPLETED` | Allowed with exactly 100 percent |
| `IN_PROGRESS` | `CANCELLED` | Allowed with reason |
| `ON_HOLD` | `IN_PROGRESS` | Allowed as resume |
| `ON_HOLD` | `CANCELLED` | Allowed with reason |
| `COMPLETED` | Any | Rejected terminal state |
| `CANCELLED` | Any | Rejected terminal state |

Validation rejects missing hold/cancel reasons, progress below 0, progress above
100, non-integer progress, unknown/protected request fields, and complete
payloads that try to send anything other than 100 percent.

## Idempotency decision

Phase 4D order progress commands do not require `Idempotency-Key`.

This follows the existing Phase 3D contract: progress commands are state-machine
transitions protected by `select_for_update` row locks, allowed-transition
validation, and append-only evidence. Retrying a successful terminal or one-way
transition becomes an invalid transition, not a second accepted command.
`IN_PROGRESS -> IN_PROGRESS` remains an intentional progress update and creates
one event/audit row per accepted command. No second incompatible idempotency
system was introduced.

PostgreSQL concurrency tests prove duplicate simultaneous start/progress,
terminal races, and completion races produce exactly one authoritative
successful transition without duplicate progress or audit evidence. SQLite and
PostgreSQL focused tests prove failed/rejected commands leave no progress or
audit timeline evidence.

## Audit and timeline evidence

Each successful Phase 4D command writes atomically:

- the allowed `TransactionOrder` progress fields;
- exactly one `OrderProgressEvent`;
- exactly one `AuditEvent`.

Focused tests verify:

- progress read endpoint shows committed progress events;
- entity audit timeline shows committed order audit events;
- Admin and Manager global audit reads remain allowed with exact `audit:view`;
- Sales global audit is denied;
- failed commands do not appear in progress or audit timelines;
- response serialization hides idempotency keys, request hashes, passwords,
  tokens, and secrets;
- progress commands do not create `InventoryTransaction` rows.

## Rollback evidence

The focused suite forces two rollback points:

- audit writer failure after the API command starts;
- failure after the order row has been saved but before progress/audit evidence
  is completed.

Both failures roll back order status, progress percentage, progress event count,
and audit event count to the pre-command baseline.

## Legacy write-path inventory

| Route or callable | Methods | Record types | Can reach `MVP_V1`? | Classification |
| --- | --- | --- | --- | --- |
| `/api/v1/orders/` via `apps.api.views.transaction_domain.orders` | `GET`, `POST` | `TransactionOrder`, `TransactionOrderItem`, `OrderStatusHistory`, `TransactionHistory`, inventory reservation | Creates `LEGACY` only | Safe unchanged |
| `/api/v1/orders/{id}/` via `apps.api.views.transaction_domain.order_detail` | `GET`, `PUT` | `TransactionOrder`, `TransactionHistory` | Could load `MVP_V1`; service now rejects mutation | Guarded |
| `/api/v1/workflows/` via `apps.api.views.transaction_domain.workflows` | `GET`, `POST` | `WorkflowApproval`, `OrderStatusHistory`, `TransactionHistory`, legacy order status fields | Could load `MVP_V1`; service now rejects mutation | Guarded |
| `/api/v1/transactions/` via `apps.api.views.transaction_domain.transactions` | `GET` | `TransactionHistory` | Read only | Safe unchanged |
| `/api/v1/admin/orders/` via `apps.api.views.admin_interface.admin_orders` | `GET`, `POST` | Same as legacy order service | Creates `LEGACY` only | Safe unchanged |
| `/api/v1/admin/orders/{id}/` via `apps.api.views.admin_interface.admin_order_detail` | `GET`, `PUT` | `TransactionOrder`, `TransactionHistory` | Could load `MVP_V1`; service now rejects mutation | Guarded |
| `/api/v1/admin/workflows/` via `apps.api.views.admin_interface.admin_workflows` | `GET`, `POST` | `WorkflowApproval`, `OrderStatusHistory`, `TransactionHistory` | Could load `MVP_V1`; service now rejects mutation | Guarded |
| Browser `/admin/orders/` | `GET`, `POST` | Same as legacy order service | Creates `LEGACY` only | Safe unchanged |
| Browser `/admin/orders/{id}/` | `GET`, `POST` | `TransactionOrder`, `TransactionHistory` | Could load `MVP_V1`; service now rejects mutation | Guarded |
| Browser `/admin/workflows/` | `GET`, `POST` | `WorkflowApproval`, `OrderStatusHistory`, `TransactionHistory` | Could load `MVP_V1`; service now rejects mutation | Guarded |
| Django model/admin registration for transaction-domain canonical evidence | Not present | `OrderProgressEvent`, `AuditEvent` | Not applicable | Not applicable |
| `TransactionHistoryService.record` | Callable | `TransactionHistory` | Caller controlled | Safe for legacy callers; canonical audit uses `AuditEvent` |

The repaired bypasses are `OrderService.update_order` and
`WorkflowService.transition_order`: both now reject `MVP_V1` orders before
writing legacy metadata, status history, workflow approval, or transaction
history.

## MVP_V1 write-boundary conclusion

SQLite and PostgreSQL evidence prove:

- `MVP_V1` order headers can only be created through accepted-quotation
  conversion;
- `MVP_V1` order-line snapshots remain immutable;
- canonical progress fields can only change through Phase 3D/4D command
  authorization;
- progress events and audit events remain append-only;
- legacy order metadata and workflow services now reject `MVP_V1` mutation;
- `LEGACY` records are not promoted or given fabricated canonical evidence.

## SQLite validation

| Check | Result |
| --- | --- |
| `python django_backend\manage.py check` | Passed; 0 issues |
| `python django_backend\manage.py makemigrations --check --dry-run` | Passed; no changes detected |
| `python -m compileall -q` on every changed Python file | Passed |
| `git diff --check` | Passed; only Windows LF-to-CRLF notices |
| Expanded focused Phase 4D SQLite suite | `11 passed, 4 skipped` |
| Phase 4A/4B/4C/4D plus relevant Phase 3D SQLite preservation | `70 passed, 9 skipped` |
| Full SQLite backend suite | `215 passed, 151 skipped` |

Skipped tests are environment-gated PostgreSQL concurrency tests and existing
environment-gated tests.

## PostgreSQL and Docker validation

Docker and PostgreSQL validation completed after Docker Desktop became
available.

Docker/port evidence:

- `docker version --format "Client={{.Client.Version}} Server={{.Server.Version}}"` returned `Client=29.4.3 Server=29.4.3`.
- Port `127.0.0.1:55439` was verified free before container creation.
- PostgreSQL version: `PostgreSQL 16.14 (Debian 16.14-1.pgdg13+1)`.
- Container: `django-phase4d-postgres16-20260913-86e2a0f`.
- Container ID: `b77057bcee90c113c4bd886ab9ec4f3bbac0b753dcd5e727718b96f1995e7c89`.
- Image: `postgres:16`.
- Container created: `2026-09-13T08:07:18.094509932Z`.
- Port mapping: `127.0.0.1:55439 -> 5432/tcp`.
- Network: `django-phase4d-net-20260913-86e2a0f`.
- Network ID: `f4ffe5439937a7a9c4bb0dd69c93f8acbf200d58fc86484e643895a7a9ad1141`.
- Volume: `django-phase4d-pg16-data-20260913-86e2a0f`.
- Volume driver: `local`.
- Volume mount: `/var/lib/postgresql/data`.
- Labels: `com.openai.task=phase4d-postgres-validation`, `com.openai.repo=Django-web-t-123`, and container baseline label `86e2a0f669acd05764ab05bdf1ec7c64524cab16`.

An initial container was recreated because it mounted an anonymous volume instead
of the named task volume. The incorrect task container and its anonymous volume
were removed before the authoritative PostgreSQL validation run. The final
validation run used the named task volume above.

PostgreSQL validation results:

| Suite | Result |
| --- | --- |
| Focused Phase 4D PostgreSQL, including four concurrency tests | `15 passed` |
| Phase 4A/4B/4C preservation, relevant Phase 3D, and Phase 3B/3C/3D migration-boundary suites | `74 passed` |
| Full PostgreSQL backend suite | `225 passed, 141 skipped` |

PostgreSQL concurrency evidence:

- Two simultaneous identical progress/start attempts produced one accepted
  `IN_PROGRESS` transition, one progress event, and one `order.progress_changed`
  audit event.
- Hold versus complete from the same `IN_PROGRESS` state produced exactly one
  accepted authoritative result and no conflicting terminal state.
- Cancel versus complete from the same `IN_PROGRESS` state produced exactly one
  accepted terminal result and no conflicting terminal state.
- Two simultaneous completion attempts produced exactly one `COMPLETED` event
  and one `order.completed` audit event.

Cleanup evidence:

- Removed only `django-phase4d-postgres16-20260913-86e2a0f`.
- Removed only `django-phase4d-net-20260913-86e2a0f`.
- Removed only `django-phase4d-pg16-data-20260913-86e2a0f`.
- Exact container inspect after cleanup returned `no such object`.
- Exact network inspect after cleanup returned `network ... not found`.
- Exact volume inspect after cleanup returned `no such volume`.
- Label query `com.openai.task=phase4d-postgres-validation` returned no containers.
- Port `127.0.0.1:55439` was verified free after cleanup.
- No command targeted any unrelated container, network, or volume.

## Git diff stat

```text
 django_backend/apps/api/canonical_permissions.py   |  5 ++
 django_backend/apps/api/canonical_urls.py          | 30 +++++++++
 .../apps/api/serializers/canonical_commands.py     | 20 ++++++
 .../apps/api/services/canonical_command_service.py | 71 +++++++++++++++++++++-
 .../apps/api/views/canonical_commands.py           | 64 +++++++++++++++++++
 .../apps/transaction_domain/order_domain.py        |  9 ++-
 django_backend/apps/transaction_domain/services.py |  9 +++
 7 files changed, 206 insertions(+), 2 deletions(-)
```

## SHA256 manifest

| Path | SHA256 |
| --- | --- |
| `django_backend/apps/api/canonical_permissions.py` | `BDD563B68E137E81A1E47E0CEDC2AFD16CAEB9258A7C1964C6185CB1267576DD` |
| `django_backend/apps/api/canonical_urls.py` | `F945FE4E79BC5EB11608860EB8A4C72AA3A2DC076B1C2C06DEAA28DFED12635A` |
| `django_backend/apps/api/serializers/canonical_commands.py` | `B5C534EABA99197615BF9A02102F51B9A3EF107C13778F5F8DD02C47839E41D5` |
| `django_backend/apps/api/services/canonical_command_service.py` | `CFED0BE27E7F877787D751DF19561E66FE500E6D6BFC40F8F7EE34788DDD4756` |
| `django_backend/apps/api/views/canonical_commands.py` | `03C0FDA3677C19730E9D3BC16D375B50C66C00C3CD33B8C4FE17860FC5DA005B` |
| `django_backend/apps/api/tests/test_phase4d_order_progress_commands.py` | `5833D9F928D205EABDCC471F8F6A8A82E6EE3DD29D83EBC5D13CE74118734630` |
| `django_backend/apps/transaction_domain/order_domain.py` | `8FB3EC9045DE326246CD65A091AC5B9A4DCF87C29C9CF25492CDE9D35547D645` |
| `django_backend/apps/transaction_domain/services.py` | `37A52AD686A85A53A2CC889BAE90536FDDD38D5B8456501CC972C48EF0C013DA` |

The report file's own stable SHA256 is reported in the task handoff after the
final report write, because embedding a file's own digest changes that digest.

## Final git status

```text
 M django_backend/apps/api/canonical_permissions.py
 M django_backend/apps/api/canonical_urls.py
 M django_backend/apps/api/serializers/canonical_commands.py
 M django_backend/apps/api/services/canonical_command_service.py
 M django_backend/apps/api/views/canonical_commands.py
 M django_backend/apps/transaction_domain/order_domain.py
 M django_backend/apps/transaction_domain/services.py
?? PHASE_4D_ORDER_PROGRESS_AUDIT_API_AND_WRITE_BOUNDARY_REPORT.md
?? django_backend/apps/api/tests/test_phase4d_order_progress_commands.py
```

## Remaining blockers

None.
